#!/usr/bin/env python3
"""Run the skill on every fixture with a real model, then check the rewrites.

Usage:
    python3 evals/run_skill.py [--model MODEL] [--out DIR] [fixture-name ...]

Each fixture's input.md is sent to `claude -p` with SKILL.md and every file in
references/ as the system prompt and the fixture's brief as the instruction.
Rewrites land in DIR (default evals/outputs/) as <fixture-name>.md, then
run_evals.py checks them. A second model call then lists any claim the
rewrite makes that the input does not state or imply; one invented claim
fails the fixture. Pass --no-judge to skip that call. Exits non-zero if
any fixture fails.

Pass --judge-only DIR to re-run only the claim check on rewrites already
saved in DIR as <fixture-name>.md, for example to test a change to the
judge prompt against earlier runs without generating new rewrites.

Pass --no-skill to produce a baseline with the same brief and no skill
loaded, into a different --out directory, then compare the two with
evals/compare_outputs.py.

Requires the Claude Code CLI (`claude`) on PATH with working credentials.
The model is claude-opus-5 unless --model says otherwise; --judge-model
picks a different model for the claim check (default stays claude-opus-5
regardless of --model, since a smaller judge over-flags).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_evals import FIXTURES_DIR, load_fixture, run_one  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_JUDGE_MODEL = "claude-opus-5"
CLAUDE_TIMEOUT = 300
MAX_RETRIES = 2

SYSTEM_HEADER = """You are running the better-writing skill. Its instructions and reference
material follow. Apply them to the user's request.

Output rules for this run: return only the final rewritten text. No preamble,
no change note, no diagnostic audit, no closing remark.
"""


JUDGE_PROMPT = """You are checking a rewrite for invented content.

The editor was given this brief:
<brief>
{brief}
</brief>

Source text:
<source>
{source}
</source>

Rewrite:
<rewrite>
{rewrite}
</rewrite>

List every claim the rewrite makes that a reader of the source and the brief
could not have taken from them: new facts, figures, events, or actors; a next
step the source never proposed; a statement about what has or has not
happened since; an opinion, verdict, thanks, joke, or aside the source does
not carry.

Also list a claim whose strength changed on the way:
- a hope, aim, or plan in the source restated as something that has happened,
  is happening, or will happen ("paving the way for a rollout" rewritten as
  "the rollout continues" or "the rollout is still to come");
- an emphasis restated as a cause ("underscores the importance of planning"
  rewritten as "planning made the difference").

Do not list: rewording, reordering, or cuts; the source's own recommendation,
opinion, or conclusion restated in plainer words at the same strength; a hope
kept as a hope ("which should help the rollout"); a change in how strongly a
claim is attributed; a fact the brief states; bracketed gap markers such as
[figure needed]; a heading that names the document's subject.

Reply with a JSON array of short strings, one per invented claim, and nothing
else. Reply with [] if there are none."""


BASELINE_HEADER = """You are a careful editor. Apply the user's request to the text.

Output rules for this run: return only the final rewritten text. No preamble,
no change note, no diagnostic audit, no closing remark.
"""


def build_system_prompt(with_skill=True):
    if not with_skill:
        return BASELINE_HEADER
    parts = [SYSTEM_HEADER, (ROOT / "SKILL.md").read_text(encoding="utf-8")]
    for ref in sorted((ROOT / "references").glob("*.md")):
        parts.append(f"\n\n<!-- references/{ref.name} -->\n\n" + ref.read_text(encoding="utf-8"))
    return "\n".join(parts)


def strip_preamble(text):
    """Remove fences and leading preamble so only the rewrite remains."""
    t = text.strip()
    # Strip markdown fences if the model wrapped the rewrite.
    t = re.sub(r"^```(?:json|markdown|md|text)?\s*\n", "", t)
    t = re.sub(r"\n```\s*$", "", t).strip()
    lines = t.splitlines()
    # Drop leading preamble lines ("Here is the rewrite:", "Sure, ...:", etc.).
    # Only colon-terminated lines match, so a legitimate opener such as
    # "Here is what changed in the second quarter." is preserved.
    preamble_re = re.compile(
        r"^(?:here(?:'s| is)|sure|certainly|of course|okay|ok)\b[^.!?]{0,60}:\s*$",
        re.I)
    while lines and preamble_re.match(lines[0].strip()):
        lines.pop(0)
    # Drop a leading "Rewrite:" label line.
    if lines and re.match(r"^rewrite\s*:\s*$", lines[0].strip(), re.I):
        lines.pop(0)
    return "\n".join(lines).strip() + ("\n" if lines else "")


def rewrite(model, system_path, brief, input_text):
    prompt = f"{brief}\n\nText:\n\n{input_text}"
    return strip_preamble(claude_text(model, prompt, system_path))


def claude_text(model, prompt, system_path=None, timeout=CLAUDE_TIMEOUT,
                retries=MAX_RETRIES):
    cmd = ["claude", "-p", prompt, "--model", model, "--tools", "",
           "--output-format", "text"]
    if system_path is not None:
        cmd += ["--system-prompt-file", str(system_path)]
    last_exc = None
    for attempt in range(retries + 1):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    check=True, timeout=timeout)
            return result.stdout.strip()
        except FileNotFoundError as exc:
            raise OSError(
                "Claude Code CLI (`claude`) not found on PATH. Install it "
                "and authenticate, then retry.") from exc
        except OSError as exc:
            # Includes ExecError, permission errors, etc.
            raise OSError(
                f"failed to run `claude` ({exc}). Check PATH and "
                "credentials, then retry.") from exc
        except subprocess.TimeoutExpired as exc:
            last_exc = exc
            print(f"  WARN claude timed out after {timeout}s "
                  f"(attempt {attempt + 1}/{retries + 1})", file=sys.stderr)
            if attempt >= retries:
                raise TimeoutError(
                    f"`claude` timed out after {timeout}s "
                    f"({retries + 1} attempts). Retry with a longer timeout "
                    "or check connectivity.") from exc
        except subprocess.CalledProcessError as exc:
            last_exc = exc
            if attempt >= retries:
                raise
            print(f"  WARN claude exited {exc.returncode} "
                  f"(attempt {attempt + 1}/{retries + 1}), retrying",
                  file=sys.stderr)
    raise last_exc  # pragma: no cover


def strip_code_fences(reply):
    """Remove markdown fences around a judge reply."""
    t = reply.strip()
    # ```json ... ``` or ``` ... ```
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", t, re.S | re.I)
    if m:
        return m.group(1).strip()
    # Loose: strip leading/trailing fence lines.
    lines = t.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


class JudgeError(Exception):
    """The judge gave no usable answer, which is not the same as a claim."""


def parse_claims(reply):
    """Return the last JSON array of non-empty strings in a judge reply.

    A judge sometimes answers, second-guesses itself, and answers again
    ("[...] Wait, that is in the source. Correcting: []"), so the final
    array is the answer. Returns None when the reply holds no such array.
    """
    cleaned = strip_code_fences(reply)
    decoder = json.JSONDecoder()
    found = None
    for i, ch in enumerate(cleaned):
        if ch != "[":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned, i)
        except json.JSONDecodeError:
            continue
        if isinstance(value, list) and all(
                isinstance(c, str) and c.strip() for c in value):
            found = [c.strip() for c in value]
    return found


def judge_added_claims(model, brief, source, rewrite, attempts=2):
    """Return the list of claims the judge found in the rewrite but not the source.

    A reply with no usable JSON array is asked again; if every attempt fails,
    JudgeError is raised so the fixture fails as a judge error rather than
    as an invented claim. The judge runs with default sampling; the Claude
    Code CLI exposes no supported temperature setting.
    """
    # The judge stays on opus unless --judge-model overrides (see main).
    prompt = JUDGE_PROMPT.format(brief=brief, source=source, rewrite=rewrite)
    reply = ""
    for attempt in range(attempts):
        reply = claude_text(model, prompt)
        print(f"  judge raw: {reply[:300]}")
        claims = parse_claims(reply)
        if claims is not None:
            return claims
        if attempt + 1 < attempts:
            print("  WARN judge reply had no JSON array of strings, asking again")
    raise JudgeError(f"no usable JSON array after {attempts} attempts: "
                     f"{reply[:200]}")


def judge_only(judge_model, out_dir, fixtures):
    """Re-judge saved rewrites; write <fixture>.claims.json next to each."""
    print(f"judge only: {judge_model} on {out_dir}")
    all_ok = True
    found = 0
    for fixture_dir in fixtures:
        rewrite_path = out_dir / f"{fixture_dir.name}.md"
        if not rewrite_path.exists():
            continue
        found += 1
        claims_path = out_dir / f"{fixture_dir.name}.claims.json"
        try:
            checks, input_text = load_fixture(fixture_dir)
            text = rewrite_path.read_text(encoding="utf-8")
            claims = judge_added_claims(judge_model, checks.get("brief", ""),
                                        input_text, text)
        except (JudgeError, OSError, TimeoutError, ValueError,
                subprocess.CalledProcessError) as exc:
            print(f"{fixture_dir.name}: FAIL judge error ({exc})")
            claims_path.unlink(missing_ok=True)
            all_ok = False
            continue
        claims_path.write_text(json.dumps(claims, indent=2) + "\n",
                               encoding="utf-8")
        if claims:
            all_ok = False
            print(f"{fixture_dir.name}: FAIL")
            for claim in claims:
                print(f"  added claim: {claim}")
        else:
            print(f"{fixture_dir.name}: no added claims")
    if not found:
        print(f"no <fixture-name>.md rewrites found in {out_dir}")
        return 2
    return 0 if all_ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--judge-model", default=None,
                        help="model for the added-claims check (default: claude-opus-5)")
    parser.add_argument("--no-judge", action="store_true",
                        help="skip the added-claims check")
    parser.add_argument("--no-skill", action="store_true",
                        help="baseline: send the brief with no skill loaded")
    parser.add_argument("--out", default=str(ROOT / "evals" / "outputs"))
    parser.add_argument("--judge-only", metavar="DIR",
                        help="only re-run the claim check on rewrites saved in DIR")
    parser.add_argument("fixtures", nargs="*", help="fixture names (default: all)")
    args = parser.parse_args()

    fixtures = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())
    if args.fixtures:
        fixtures = [f for f in fixtures if f.name in args.fixtures]
        missing = set(args.fixtures) - {f.name for f in fixtures}
        if missing:
            print(f"unknown fixtures: {', '.join(sorted(missing))}")
            return 2

    judge_model = args.judge_model or DEFAULT_JUDGE_MODEL
    if args.judge_only:
        # Read-and-judge only: never create or touch the --out directory.
        return judge_only(judge_model, Path(args.judge_only), fixtures)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    system_path = out_dir / "_system_prompt.md"
    system_path.write_text(build_system_prompt(not args.no_skill), encoding="utf-8")

    print(f"model: {args.model}" + ("" if args.no_judge else f", judge: {judge_model}")
          + (", no skill loaded (baseline)" if args.no_skill else ""))

    all_ok = True
    for fixture_dir in fixtures:
        claims_path = out_dir / f"{fixture_dir.name}.claims.json"
        try:
            checks, input_text = load_fixture(fixture_dir)
        except OSError as exc:
            print(f"{fixture_dir.name}: FAIL (bad fixture: {exc})")
            all_ok = False
            continue
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"{fixture_dir.name}: FAIL (bad fixture JSON: {exc})")
            all_ok = False
            continue
        except KeyError as exc:
            print(f"{fixture_dir.name}: FAIL (bad fixture: missing {exc})")
            all_ok = False
            continue
        try:
            brief = checks["brief"]
        except KeyError:
            print(f"{fixture_dir.name}: FAIL (bad fixture: missing 'brief')")
            all_ok = False
            continue
        try:
            text = rewrite(args.model, system_path, brief, input_text)
        except subprocess.CalledProcessError as exc:
            print(f"{fixture_dir.name}: FAIL (claude exited {exc.returncode})")
            if exc.stderr:
                print(exc.stderr.strip())
            # Refresh stale claims so a previous pass does not linger.
            try:
                claims_path.unlink(missing_ok=True)
            except OSError:
                pass
            all_ok = False
            continue
        except (OSError, TimeoutError) as exc:
            print(f"{fixture_dir.name}: FAIL ({exc})")
            try:
                claims_path.unlink(missing_ok=True)
            except OSError:
                pass
            all_ok = False
            continue
        rewrite_path = out_dir / f"{fixture_dir.name}.md"
        rewrite_path.write_text(text, encoding="utf-8")
        try:
            ok = run_one(fixture_dir, rewrite_path)
        except (OSError, ValueError, KeyError) as exc:
            print(f"{fixture_dir.name}: FAIL (bad fixture: {exc})")
            ok = False
        all_ok &= ok
        if args.no_judge:
            # Delete stale claims so reruns without a judge do not look judged.
            try:
                claims_path.unlink(missing_ok=True)
            except OSError as exc:
                print(f"  WARN could not delete stale {claims_path}: {exc}")
            continue
        try:
            claims = judge_added_claims(judge_model, brief, input_text, text)
        except JudgeError as exc:
            print(f"  FAIL judge error ({exc})")
            try:
                claims_path.unlink(missing_ok=True)
            except OSError:
                pass
            all_ok = False
            continue
        except subprocess.CalledProcessError as exc:
            print(f"  FAIL judge (claude exited {exc.returncode})")
            try:
                claims_path.unlink(missing_ok=True)
            except OSError:
                pass
            all_ok = False
            continue
        except (OSError, TimeoutError) as exc:
            print(f"  FAIL judge ({exc})")
            try:
                claims_path.unlink(missing_ok=True)
            except OSError:
                pass
            all_ok = False
            continue
        claims_path.write_text(
            json.dumps(claims, indent=2) + "\n", encoding="utf-8")
        if claims:
            all_ok = False
            for claim in claims:
                print(f"  FAIL added claim: {claim}")
        else:
            print("  judge: no added claims")

    print(f"rewrites saved in {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
