#!/usr/bin/env python3
"""Pairwise comparison of two sets of rewrites with a model as judge.

Usage:
    python3 evals/compare_outputs.py [--model MODEL] <dir-a> <dir-b> [fixture-name ...]

For every fixture, the judge sees the brief, the source text, and the two
rewrites, unlabelled and in both orders, and says which better serves the
brief's reader. A pair counts as a win only if the same rewrite wins both
orders; a split is a tie. Typical use: dir-a from `run_skill.py --no-skill`
and dir-b from `run_skill.py`, to show the skill changes the output for the
better and not just differently.

Judges prefer low-perplexity text and the first item shown, and they agree
with human writing preferences only about three quarters of the time, so a
loss here is a flag to read the two outputs, not a verdict.

Requires the Claude Code CLI (`claude`) on PATH with working credentials.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_evals import FIXTURES_DIR, load_fixture  # noqa: E402
from run_skill import ISOLATION_FLAGS, JUDGE_SYSTEM  # noqa: E402

CLAUDE_TIMEOUT = 300
MAX_RETRIES = 2

PROMPT = """Two editors were given the same brief and the same text. Judge which
rewrite better serves the reader the brief describes. Weigh, in this order:
every fact from the source kept and nothing added; the register the brief
asks for; directness and specificity; whether it reads as written by one
person for one reader. Do not reward length, formatting, or polish for its
own sake.

Brief: {brief}

Source text:
<source>
{source}
</source>

Rewrite 1:
<rewrite1>
{first}
</rewrite1>

Rewrite 2:
<rewrite2>
{second}
</rewrite2>

Reply with exactly one character: 1 or 2."""


def _one_verdict(text):
    """Return the only rewrite that text points at, or None.

    Counts both "Rewrite N" and a standalone 1 or 2 (not part of "1.2" or
    "v2"), so "Rewrite 1 pads, so 2." points at two rewrites, not one.
    """
    named = set(re.findall(r"rewrite\s*([12])", text, re.I))
    rest = re.sub(r"rewrite\s*[12]", " ", text, flags=re.I)
    # A full stop after the digit ends a sentence ("so 2."); one between
    # digits makes a version or a decimal ("1.2"), which is not a verdict.
    found = named | set(re.findall(r"(?<!\w)(?<!\d\.)([12])(?!\w|\.\d)", rest))
    return found.pop() if len(found) == 1 else None


def parse_verdict(reply):
    """Return "1" or "2" from a judge reply, or None when it is unclear.

    The prompt asks for one character, so a final line that holds only the
    verdict wins: "2", "**1**", "Rewrite 2.", "Answer: **2**". A longer
    final line ("Rewrite 1 pads.") may be reasoning, not the verdict, so it
    gets no such weight. Otherwise the whole reply must
    point at exactly one rewrite. A reply that points at both, such as
    "Rewrite 2 is better because Rewrite 1 pads.", gives None: taking
    either mention can read the verdict the wrong way round (issue #80),
    and the caller asks again or counts a skip. A single incidental digit
    ("keeps both 2 dates") can still be misread; the prompt makes such
    replies rare.
    """
    reply = reply.strip()
    if not reply:
        return None
    last_line = reply.splitlines()[-1].strip()
    match = re.fullmatch(r"[\W_]*(?:(?:answer|verdict|winner|choice)[\W_]*)?"
                         r"(?:rewrite\s*)?([12])[\W_]*", last_line, re.I)
    if match:
        return match.group(1)
    return _one_verdict(reply)


def ask(model, prompt, timeout=CLAUDE_TIMEOUT, retries=MAX_RETRIES):
    cmd = ["claude", "-p", prompt, "--model", model, "--tools", "",
           "--output-format", "text", *ISOLATION_FLAGS,
           "--system-prompt", JUDGE_SYSTEM]
    for attempt in range(retries + 1):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True,
                timeout=timeout)
        except FileNotFoundError as exc:
            print(f"  FAIL judge: `claude` not found on PATH ({exc}). "
                  "Install the Claude Code CLI with credentials, then retry.")
            return None
        except OSError as exc:
            print(f"  FAIL judge: failed to run `claude` ({exc}). "
                  "Check PATH and credentials, then retry.")
            return None
        except subprocess.TimeoutExpired:
            print(f"  WARN judge timed out after {timeout}s "
                  f"(attempt {attempt + 1}/{retries + 1})")
            if attempt >= retries:
                print(f"  FAIL judge: timed out after {timeout}s "
                      f"({retries + 1} attempts).")
                return None
            continue
        except subprocess.CalledProcessError as exc:
            print(f"  WARN judge: claude exited {exc.returncode} "
                  f"(attempt {attempt + 1}/{retries + 1})")
            if exc.stderr:
                print(f"  judge stderr: {exc.stderr.strip()[:300]}")
            if attempt >= retries:
                print(f"  FAIL judge: claude exited {exc.returncode} "
                      f"after {retries + 1} attempts.")
                return None
            continue
        reply = result.stdout.strip()
        print(f"  judge raw: {reply[:200]}")
        verdict = parse_verdict(reply)
        if verdict is not None:
            return verdict
        print(f"  WARN judge reply had no single 1/2 verdict "
              f"(attempt {attempt + 1}/{retries + 1}): {reply[:200]}")
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", default="claude-opus-5")
    parser.add_argument("dir_a")
    parser.add_argument("dir_b")
    parser.add_argument("fixtures", nargs="*")
    args = parser.parse_args()

    dir_a, dir_b = Path(args.dir_a), Path(args.dir_b)
    fixtures = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())
    if args.fixtures:
        unknown = set(args.fixtures) - {f.name for f in fixtures}
        if unknown:
            print(f"unknown fixtures: {', '.join(sorted(unknown))}")
            return 2
        fixtures = [f for f in fixtures if f.name in args.fixtures]

    print(f"judge: {args.model}, A = {dir_a}, B = {dir_b}")
    tally = {"A": 0, "B": 0, "tie": 0, "skip": 0}
    missing = 0
    for fixture_dir in fixtures:
        path_a, path_b = dir_a / f"{fixture_dir.name}.md", dir_b / f"{fixture_dir.name}.md"
        if not (path_a.exists() and path_b.exists()):
            print(f"{fixture_dir.name}: skipped (missing rewrite)")
            tally["skip"] += 1
            missing += 1
            continue
        try:
            checks, source = load_fixture(fixture_dir)
        except OSError as exc:
            print(f"{fixture_dir.name}: skipped (bad fixture: {exc})")
            tally["skip"] += 1
            continue
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"{fixture_dir.name}: skipped (bad fixture JSON: {exc})")
            tally["skip"] += 1
            continue
        except KeyError as exc:
            print(f"{fixture_dir.name}: skipped (bad fixture: missing {exc})")
            tally["skip"] += 1
            continue
        try:
            brief = checks["brief"]
        except KeyError:
            print(f"{fixture_dir.name}: skipped (bad fixture: missing 'brief')")
            tally["skip"] += 1
            continue
        try:
            text_a = path_a.read_text(encoding="utf-8")
            text_b = path_b.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"{fixture_dir.name}: skipped (cannot read rewrite: {exc})")
            tally["skip"] += 1
            continue
        common = dict(brief=brief, source=source)
        first = ask(args.model, PROMPT.format(first=text_a, second=text_b, **common))
        second = ask(args.model, PROMPT.format(first=text_b, second=text_a, **common))
        if first == "1" and second == "2":
            verdict = "A"
        elif first == "2" and second == "1":
            verdict = "B"
        elif first in ("1", "2") and second in ("1", "2"):
            verdict = "tie"
        else:
            verdict = "skip"
            print(f"{fixture_dir.name}: skipped "
                  f"(orders: {first or '?'}, {second or '?'})")
            tally[verdict] += 1
            continue
        tally[verdict] += 1
        print(f"{fixture_dir.name}: {verdict} (orders: {first or '?'}, {second or '?'})")

    print(f"A wins {tally['A']}, B wins {tally['B']}, "
          f"ties {tally['tie']}, skips {tally['skip']}")
    if missing:
        return 1
    if tally["skip"] and (tally["A"] + tally["B"] + tally["tie"] == 0):
        # All skipped: no signal, fail loudly.
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
