#!/usr/bin/env python3
"""Run the skill on every fixture with a real model, then check the rewrites.

Usage:
    python3 evals/run_skill.py [--model MODEL] [--out DIR] [fixture-name ...]
    python3 evals/run_skill.py --arm both --repeats 5
    python3 evals/run_skill.py --split dev --arm both --repeats 5

Each fixture's input.md is sent to `claude -p` with the skill loaded and the
fixture's brief as the instruction. Rewrites land in DIR (default
evals/outputs/) as <fixture-name>.md, then run_evals.py checks them. A second
model call then lists any claim the rewrite makes that the input does not
state or imply; one invented claim fails the fixture. Pass --no-judge to skip
that call. Exits non-zero if any fixture fails.

Two loading arms measure the real config instead of only an upper bound:

- always-on (default): the system prompt concatenates SKILL.md plus every
  file in references/. This is the historical behaviour; real harnesses never
  see this much context at once, so its pass rate is an upper bound.
- progressive: the system prompt carries only the skill's listing (its name
  and the SKILL.md frontmatter description, ~100 tokens, which is what a
  harness shows the model) plus SKILL.md, and the model may Read
  references/*.md on demand from a staging dir holding only the skill
  (<out>/_skill_root, rebuilt every run), the way a real harness loads
  SKILL.md on trigger and individual references on demand. Staging keeps the
  grading rubric (checks.json, examples/) out of the Read tool's reach.

Pass --arm progressive for the real-config arm only, or --arm both to run
the two side by side and report the paired per-fixture difference. Both
arms read the whole of SKILL.md, frontmatter included, so both see a change
to the frontmatter description; the progressive arm also gets it as the
listing line in its header. Neither arm decides whether to load the skill:
run_triggers.py measures that.

Pass --repeats K to generate K independent rewrites per fixture per arm
(default 1; use 5 or more when sizing a skill change, and more if a
fixture's pass rate swings between runs). Rewrites are saved as
<fixture>.r<k>.md under <out>/<arm>/ with a top-level summary.json holding
per-fixture pass rates with Wilson 95% intervals, each arm's overall rate
with a t interval over per-fixture rates, and the paired
progressive-minus-always-on difference
with its interval. With the default --repeats 1 and --arm always-on the
layout is unchanged (<fixture-name>.md next to _system_prompt.md) plus a
summary.json.

Pass --split dev to run only the tuned dev fixtures, --split heldout for the
never-read held-out set (see evals/splits.json), or --split all (default).
Tune on dev; confirm once on heldout.

Pass --judge-only DIR to re-run only the claim check on rewrites already
saved in DIR as <fixture-name>.md, for example to test a change to the
judge prompt against earlier runs without generating new rewrites.

Pass --baseline SUMMARY to print per-fixture pass-rate changes against a
saved summary.json (the committed reference is evals/baselines/<model>.
summary.json). Add --compare-summary FILE to compare a saved run instead of
generating one.

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
import math
import re
import shutil
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_evals import FIXTURES_DIR, load_fixture, run_one  # noqa: E402
# One frontmatter parser for the repo checks and the eval runners.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from validate import parse_simple_frontmatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "better-writing"
SPLITS_PATH = Path(__file__).resolve().parent / "splits.json"

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_JUDGE_MODEL = "claude-opus-5"
CLAUDE_TIMEOUT = 300
MAX_RETRIES = 2

ARMS = ("always-on", "progressive")

# One output rule for every arm and the baseline, so the arms differ only in
# how the skill is loaded. Review fixtures ask for findings, not a rewrite.
# The skill asks for a change note in some cases, and the checker and judge
# score the whole reply as the text, so the rule has to say it wins: without
# that, the model followed the skill and appended the note (issue #57). The
# wording stays generic so it hints at no fixture.
OUTPUT_RULES = """Output rules for this run: return only what the brief asks for. For a rewrite
or a draft, that is the final text alone: no preamble, no change note, no
diagnostic audit, no closing remark. If other instructions ask for a change
note or a note to the user beside a rewrite or a draft, leave the note out,
and do not move what it would say into the text. For a review, it is the
findings alone, with no rewritten version.
"""

SYSTEM_HEADER = """You are running the better-writing skill. Its instructions and reference
material follow. Apply them to the user's request.

""" + OUTPUT_RULES


def git(*args):
    """Run a read-only git command in the repo; return the CompletedProcess.

    --no-optional-locks keeps `git status` from taking the index lock, so a
    concurrent git command in the same checkout does not fail.
    """
    return subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), *args],
                          capture_output=True, text=True)


# What a run reads: the skill, the eval runner and fixtures, and the plugin
# manifest (the progressive arm's fallback description). The committed
# reference summaries are outputs, not inputs.
MEASURED_PATHS = ("skills", "evals", ".claude-plugin", ":(exclude)evals/baselines")


def is_run_output(status_line):
    """True for an untracked directory that an earlier run wrote.

    `git status --porcelain` lists an untracked directory as "?? path/".
    A run's --out holds summary.json, _system_prompt.md, or _skill_root, so
    an old --out under evals/ does not count as a change to the inputs.
    """
    if not status_line.startswith("?? ") or not status_line.endswith("/"):
        return False
    folder = ROOT / status_line[3:].strip('"')
    return any((folder / name).exists()
               for name in ("summary.json", "_system_prompt.md", "_skill_root"))


def run_metadata(out_dir=None):
    """Record what a summary measured: skill version, commit, tree state, date.

    Call it before the run writes anything, so the record describes the
    text the run reads. A saved summary is only comparable to another run
    of the same skill text, so the version from SKILL.md and the git commit
    travel with it. `dirty` is True when MEASURED_PATHS had uncommitted
    changes, so the commit does not hold the text the run measured (issue
    #78); `out_dir`, when it sits inside the repo, does not count. Each is
    None when it cannot be read.
    """
    try:
        front = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8-sig")
        match = re.search(r'^\s+version:\s*"?([^"\s#]+)"?', front, re.M)
        version = match.group(1) if match else None
    except OSError:
        version = None
    commit = dirty = None
    try:
        head = git("rev-parse", "--short", "HEAD")
        if head.returncode == 0:
            commit = head.stdout.strip() or None
        if commit is not None:
            paths = list(MEASURED_PATHS)
            rel = None
            if out_dir is not None:
                try:
                    rel = Path(out_dir).resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    rel = None
            # Skip the exclude when --out holds a measured path ("--out evals"),
            # or it would hide real edits.
            measured = ("skills", "evals", ".claude-plugin")
            if rel and rel != "." and not any(
                    m == rel or m.startswith(rel + "/") for m in measured):
                paths.append(f":(exclude,literal){rel}")
            status = git("status", "--porcelain", "--", *paths)
            if status.returncode == 0:
                dirty = any(not is_run_output(line)
                            for line in status.stdout.splitlines() if line.strip())
    except OSError:
        pass
    return {"skill_version": version, "commit": commit, "dirty": dirty,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}


def commit_on_default_branch(commit="HEAD"):
    """Return (branch, True/False) for whether HEAD is on origin's default
    branch, or (branch, None) when git cannot tell: no remote, no history,
    or a shallow clone, where a cut history makes the ancestry test fail.
    The answer is only as fresh as the last fetch.
    """
    try:
        shallow = git("rev-parse", "--is-shallow-repository")
        if shallow.returncode == 0 and shallow.stdout.strip() == "true":
            return ("origin/main", None)
        head = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD")
        branch = head.stdout.strip() if head.returncode == 0 else "origin/main"
        result = git("merge-base", "--is-ancestor", commit or "HEAD", branch)
    except OSError:
        return ("origin/main", None)
    if result.returncode in (0, 1):
        return (branch, result.returncode == 0)
    return (branch, None)


def reference_warnings(meta, branch, on_branch, end=None):
    """Say why a summary should not be committed as a reference as it is.

    The reference's `commit` must hold the skill text and runner it measured
    and stay reachable. A dirty tree breaks the first. A commit off the
    default branch breaks the second once the branch is squash-merged and
    deleted: the reference then names a commit nobody can check out.
    `end` is the same record read again when the run finished: the run
    reads fixtures as it goes, so a checkout that moved or became dirty
    during the run also breaks the first.
    """
    warnings = []
    commit = meta.get("commit")
    if end is not None and (end.get("commit") != commit
                            or (end.get("dirty") and not meta.get("dirty"))):
        warnings.append(
            f"the checkout changed during the run (commit {commit} at the "
            f"start, {end.get('commit')} at the end, or new uncommitted "
            "changes): the summary may not describe the text every fixture "
            "read. Do not commit it as a reference.")
    if meta.get("dirty"):
        warnings.append(
            f"uncommitted changes under skills/, evals/ or .claude-plugin/ "
            f"when the run started: commit {commit} "
            "does not hold the text this run measured. Do not commit this "
            "summary as a reference.")
    if on_branch is False:
        warnings.append(
            f"commit {commit} is not on {branch}. If this summary becomes a "
            "reference and the branch is squash-merged, set its commit to "
            "the merge commit on the default branch, or re-record.")
    return warnings


def skill_description():
    """Return the skill listing line the progressive arm ships (~100 tokens).

    Harnesses list a skill by the `description` in its SKILL.md frontmatter
    and load the rest of SKILL.md only on trigger, so the progressive arm
    starts from that line (issue #75). The plugin manifest's description is
    a different, shorter text that no harness shows the model; it is only
    the fallback when SKILL.md has no frontmatter description.
    """
    try:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8-sig")
    except OSError:
        text = ""
    # Parse the frontmatter the way scripts/validate.py does, so a folded,
    # wrapped or quoted description gives the same text here. read_text
    # already turns CRLF into LF; the replace matches validate.py, which
    # reads bytes.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    front = re.match(r"---\n(.*?)\n---(?:\n|$)", text, re.S)
    desc = parse_simple_frontmatter(front.group(1)).get("description") if front else None
    if isinstance(desc, str) and desc.strip():
        return desc.strip()
    manifest = ROOT / ".claude-plugin" / "plugin.json"
    try:
        desc = json.loads(manifest.read_text(encoding="utf-8")).get("description")
    except (OSError, ValueError, AttributeError):
        desc = None
    if isinstance(desc, str) and desc.strip():
        return desc.strip()
    return "better-writing"


def progressive_footer():
    """List the reference files the model may fetch on demand."""
    names = sorted(p.name for p in (SKILL_DIR / "references").glob("*.md"))
    listed = "\n".join(f"- references/{name}" for name in names)
    return f"""Reference files you may read on demand with the Read tool, from the
working directory, when this brief calls for them; read only the ones you
need, never the whole set up front. The working directory holds the skill
(SKILL.md) and its references/ only: stay inside it.

{listed}

""" + OUTPUT_RULES


def stage_skill_root(out_dir):
    """Copy SKILL.md and references/ into out_dir/_skill_root; return it.

    The progressive arm runs with cwd here so the Read tool sees exactly
    what a real harness serves — the skill and its references — and never
    the grading rubric (evals/fixtures/*/checks.json, evals/examples/*),
    which lives outside the staging dir. Rebuilt on every run, so a repeat
    always measures the current working tree.
    """
    stage = Path(out_dir) / "_skill_root"
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SKILL_DIR / "SKILL.md", stage / "SKILL.md")
    shutil.copytree(SKILL_DIR / "references", stage / "references")
    return stage


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

""" + OUTPUT_RULES


# Keep the user's own settings out of eval runs: without these, `claude -p`
# loads ~/.claude/CLAUDE.md, auto-memory, plugins, and MCP servers, so results
# depend on whose machine ran them.
ISOLATION_FLAGS = ["--setting-sources", "", "--strict-mcp-config",
                   "--no-session-persistence"]
JUDGE_SYSTEM = "You are an evaluation judge. Follow the prompt's reply format exactly."


def build_system_prompt(with_skill=True, arm="always-on"):
    if not with_skill:
        return BASELINE_HEADER
    if arm == "progressive":
        # Real-config arm: the skill listing plus SKILL.md only. References
        # stay on disk for the model to fetch with the Read tool, while
        # always-on concatenates all of them. Both arms read SKILL.md whole,
        # so a change to it (the description included) reaches both. The
        # arms also differ in the header (this one lists the description
        # first), the footer, the Read tool, and which references the model
        # reads.
        header = ("You are running the better-writing skill.\n"
                  f"Installed skill: better-writing — "
                  f"\"{skill_description()}\"\n"
                  "Its instructions follow. Apply them to the user's request.\n")
        return "\n".join([header,
                          (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"),
                          progressive_footer()])
    if arm != "always-on":
        raise ValueError(f"unknown arm {arm!r} (known: {', '.join(ARMS)})")
    parts = [SYSTEM_HEADER, (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")]
    for ref in sorted((SKILL_DIR / "references").glob("*.md")):
        parts.append(f"\n\n<!-- references/{ref.name} -->\n\n" + ref.read_text(encoding="utf-8"))
    return "\n".join(parts)


def load_split(split):
    """Return the fixture names for a --split value, or None for 'all'."""
    if split == "all":
        return None
    try:
        splits = json.loads(SPLITS_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read {SPLITS_PATH}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"cannot parse {SPLITS_PATH}: {exc}") from exc
    try:
        names = splits[split]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            f"unknown split {split!r} (known: dev, heldout, all)") from exc
    if not isinstance(names, list) or not all(
            isinstance(n, str) and n for n in names):
        raise ValueError(f"splits.json[{split!r}] must be a list of names")
    return list(names)


def wilson_interval(count, n, z=1.96):
    """Wilson score 95% interval for a binomial proportion. Stdlib only."""
    if n <= 0:
        return (0.0, 1.0)
    p = count / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def newcombe_diff_interval(count1, n1, count2, n2, z=1.96):
    """Newcombe (Wilson-based) 95% interval for p1 - p2, independent samples.

    Used for the per-fixture progressive-minus-always-on difference over K
    repeats: the two arms' repeats are independent generations.
    """
    if n1 <= 0 or n2 <= 0:
        return (0.0, 0.0)
    p1, p2 = count1 / n1, count2 / n2
    lo1, hi1 = wilson_interval(count1, n1, z)
    lo2, hi2 = wilson_interval(count2, n2, z)
    diff = p1 - p2
    lo = diff - math.sqrt((p1 - lo1) ** 2 + (hi2 - p2) ** 2)
    hi = diff + math.sqrt((hi1 - p1) ** 2 + (p2 - lo2) ** 2)
    return (max(-1.0, lo), min(1.0, hi))


# Two-sided 95% t critical values by degrees of freedom; df > 30 uses 1.96.
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
        7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
        13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101,
        19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064,
        25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}


def paired_mean_diff_interval(diffs):
    """Mean of per-fixture values with a 95% t interval.

    `diffs` is one value per fixture: a progressive-minus-always-on
    difference, a change against a baseline, or a pass rate. Repeats of one
    fixture are correlated, so the fixture, not the run, is the unit of
    sampling (issue #72). Returns (mean, lo, hi). One fixture, or values
    that are all equal, give a zero-width interval at the mean; the report
    prints that case as "no interval" rather than as certainty.
    """
    diffs = list(diffs)
    if not diffs:
        return (0.0, 0.0, 0.0)
    avg = statistics.mean(diffs)
    if len(diffs) < 2:
        return (avg, avg, avg)
    spread = statistics.stdev(diffs)
    # Changes that are equal on paper can differ in the last bit (0.6 - 0.4
    # against 0.8 - 0.6), so a spread this small counts as none.
    if spread < 1e-9:
        return (avg, avg, avg)
    t = _T95.get(len(diffs) - 1, 1.96)
    half = t * spread / math.sqrt(len(diffs))
    return (avg, avg - half, avg + half)


# Recorded beside each arm's overall ci95, since summaries written before
# issue #72 hold a pooled Wilson interval under the same key.
CI95_METHOD = "t over per-fixture rates"


def clamp_interval(lo, hi, low, high):
    """Cut an interval to [low, high]; return (lo, hi, whether it was cut)."""
    return (max(low, lo), min(high, hi), lo < low or hi > high)


# A fence line that can open a wrapper around the whole reply.
WRAPPER_FENCE = re.compile(r"^```(json|markdown|md|text)?\s*$", re.I)


def unwrap_fence(lines):
    """Return the lines inside a fence that wraps the whole reply, or None.

    The first line must open a fence (no label, or json, markdown, md, text)
    and the last line must be a bare closing fence. With fence lines between
    them the pair is ambiguous: the first line may open a real code block
    and the last close another (issue #74). Inside a real wrapper the first
    inner fence opens a block, so it carries a label ("```bash"); a bare
    first inner fence closes a block that the first line opened. So the
    reply is unwrapped only when the inner fences pair up and the first one
    has a label. A wrapper whose first inner block has no label is left
    alone, fences and all.
    """
    if len(lines) < 2 or lines[-1].strip() != "```":
        return None
    if not WRAPPER_FENCE.match(lines[0].strip()):
        return None
    inner = lines[1:-1]
    fences = [line.strip() for line in inner if line.strip().startswith("```")]
    if not fences:
        return inner
    if len(fences) % 2 == 0 and fences[0] != "```":
        return inner
    return None


def strip_preamble(text):
    """Remove a wrapping fence and leading preamble so only the rewrite remains."""
    lines = text.strip().splitlines()
    inner = unwrap_fence(lines)
    unwrapped = inner is not None
    if unwrapped:
        lines = inner
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
    while lines and not lines[0].strip():
        lines.pop(0)
    # A preamble often introduces a fenced block ("Here's the rewrite:\n```"),
    # so the wrapper only surfaces once the preamble is gone.
    if not unwrapped:
        inner = unwrap_fence(lines)
        if inner is not None:
            lines = inner
    result = "\n".join(lines).strip()
    return result + ("\n" if result else "")


def rewrite(model, system_path, brief, input_text, tools="", cwd=None):
    prompt = f"{brief}\n\nText:\n\n{input_text}"
    return strip_preamble(claude_text(model, prompt, system_path, tools=tools,
                                      cwd=cwd))


def claude_text(model, prompt, system_path=None, timeout=CLAUDE_TIMEOUT,
                retries=MAX_RETRIES, tools="", cwd=None):
    # tools="" disables every tool (the always-on arm and the judge: the
    # whole skill already sits in the system prompt, so there is nothing to
    # fetch). The progressive arm passes tools="Read" so the model can fetch
    # references/*.md on demand from cwd (the per-run <out>/_skill_root
    # staging dir), the way a real harness loads references only when the
    # skill points at them.
    cmd = ["claude", "-p", prompt, "--model", model, "--tools", tools,
           "--output-format", "text", *ISOLATION_FLAGS]
    if system_path is not None:
        cmd += ["--system-prompt-file", str(system_path)]
    else:
        cmd += ["--system-prompt", JUDGE_SYSTEM]
    last_exc = None
    for attempt in range(retries + 1):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    check=True, timeout=timeout, cwd=cwd)
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
            if checks.get("mode") == "review":
                print(f"{fixture_dir.name}: judge skipped (review mode)")
                claims_path.unlink(missing_ok=True)
                continue
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


def generate_and_score(model, judge_model, system_path, tools, cwd,
                        fixture_dir, rewrite_path, claims_path, no_judge,
                        tag=""):
    """Generate one rewrite for a fixture and score it. Returns True on pass.

    `tag` labels progress lines when one fixture is generated several times
    (for example "r3/5"). Prints the checker and judge verdicts. A rewrite
    that fails to generate, fails its checks, or gains a judge claim returns
    False; generation and judge failures also remove any stale rewrite and
    claims at the target paths so later checks do not score old text.
    """
    label = f"{fixture_dir.name}{tag}"
    try:
        checks, input_text = load_fixture(fixture_dir)
    except OSError as exc:
        print(f"{label}: FAIL (bad fixture: {exc})")
        return False
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"{label}: FAIL (bad fixture JSON: {exc})")
        return False
    except KeyError as exc:
        print(f"{label}: FAIL (bad fixture: missing {exc})")
        return False
    try:
        brief = checks["brief"]
    except KeyError:
        print(f"{label}: FAIL (bad fixture: missing 'brief')")
        return False
    try:
        text = rewrite(model, system_path, brief, input_text,
                       tools=tools, cwd=cwd)
    except subprocess.CalledProcessError as exc:
        print(f"{label}: FAIL (claude exited {exc.returncode})")
        if exc.stderr:
            print(exc.stderr.strip())
        # Remove the previous run's rewrite and claims so later checks
        # and compare_outputs.py do not score stale text.
        try:
            claims_path.unlink(missing_ok=True)
            rewrite_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    except (OSError, TimeoutError) as exc:
        print(f"{label}: FAIL ({exc})")
        try:
            claims_path.unlink(missing_ok=True)
            rewrite_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    rewrite_path.write_text(text, encoding="utf-8")
    try:
        ok = run_one(fixture_dir, rewrite_path)
    except (OSError, ValueError, KeyError) as exc:
        print(f"{label}: FAIL (bad fixture: {exc})")
        ok = False
    if no_judge or checks.get("mode") == "review":
        # A review's findings are verdicts on the source by design, so the
        # added-claims judge does not apply to them.
        # Delete stale claims so reruns without a judge do not look judged.
        try:
            claims_path.unlink(missing_ok=True)
        except OSError as exc:
            print(f"  WARN could not delete stale {claims_path}: {exc}")
        return ok
    try:
        claims = judge_added_claims(judge_model, brief, input_text, text)
    except JudgeError as exc:
        print(f"  FAIL judge error ({exc})")
        try:
            claims_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    except subprocess.CalledProcessError as exc:
        print(f"  FAIL judge (claude exited {exc.returncode})")
        try:
            claims_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    except (OSError, TimeoutError) as exc:
        print(f"  FAIL judge ({exc})")
        try:
            claims_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    claims_path.write_text(
        json.dumps(claims, indent=2) + "\n", encoding="utf-8")
    if claims:
        for claim in claims:
            print(f"  FAIL added claim: {claim}")
        return False
    print("  judge: no added claims")
    return ok


def build_summary(model, judge_model, no_judge, arms, repeats, split,
                  results, metadata=None):
    """Assemble the summary.json payload from per-fixture per-arm passes.

    `results` maps fixture name to {arm: [bool, ...]}. Per-fixture rates
    carry Wilson 95% intervals. Each arm's overall rate carries a t interval
    over per-fixture rates, since repeats of one fixture are correlated.
    The two-arm difference carries a per-fixture Newcombe interval plus a
    paired mean difference over fixtures with a t interval.
    """
    fixtures = {}
    for name in sorted(results):
        entry = {}
        for arm in arms:
            passes = results[name].get(arm, [])
            count = sum(1 for p in passes if p)
            entry[arm] = {"pass": count, "n": len(passes),
                          "rate": count / len(passes) if passes else 0.0,
                          "ci95": list(wilson_interval(count, len(passes)))}
        if "always-on" in entry and "progressive" in entry:
            a, p = entry["always-on"], entry["progressive"]
            diff = p["rate"] - a["rate"]
            entry["diff_progressive_minus_always_on"] = diff
            entry["diff_ci95"] = list(newcombe_diff_interval(
                p["pass"], p["n"], a["pass"], a["n"]))
        fixtures[name] = entry
    overall = {}
    for arm in arms:
        total_pass = sum(v[arm]["pass"] for v in fixtures.values())
        total_n = sum(v[arm]["n"] for v in fixtures.values())
        # The interval is over per-fixture rates, not pooled runs: repeats
        # of one fixture mostly pass or fail together, so a pooled Wilson
        # interval over every run comes out too narrow.
        rates = [v[arm]["rate"] for v in fixtures.values() if v[arm]["n"]]
        mean, lo, hi = paired_mean_diff_interval(rates)
        lo, hi, clamped = clamp_interval(lo, hi, 0.0, 1.0)
        overall[arm] = {"pass": total_pass, "n": total_n,
                        "rate": total_pass / total_n if total_n else 0.0,
                        "fixture_mean": mean,
                        "ci95": [lo, hi], "ci95_method": CI95_METHOD,
                        "ci95_clamped": clamped}
    overall["n_fixtures"] = len(fixtures)
    if "always-on" in overall and "progressive" in overall:
        diffs = [fixtures[n]["diff_progressive_minus_always_on"]
                 for n in fixtures]
        avg, lo, hi = paired_mean_diff_interval(diffs)
        lo, hi, clamped = clamp_interval(lo, hi, -1.0, 1.0)
        overall["paired_mean_diff"] = avg
        overall["paired_ci95"] = [lo, hi]
        overall["paired_ci95_clamped"] = clamped
    return {"model": model, "judge_model": None if no_judge else judge_model,
            "no_judge": no_judge, "arms": list(arms), "repeats": repeats,
            "split": split, **(metadata or run_metadata()), "fixtures": fixtures,
            "overall": overall}


def interval_text(lo, hi, count, sign=True, clamped=False):
    """Format a 95% t interval over `count` fixtures.

    A zero-width interval means one fixture or identical values, which says
    nothing about the spread, so it prints as "no interval" instead. A
    clamped interval says so: near 0 or 1 the symmetric t interval runs
    past the possible range, and the cut bound is approximate.
    """
    if count == 0:
        return "(no interval: no fixtures)"
    if count < 2:
        return "(no interval: one fixture)"
    # paired_mean_diff_interval already returns lo == hi for a spread under
    # 1e-9; this catches the same case for a caller that built lo and hi
    # another way. Rate data cannot produce a spread near that threshold.
    if math.isclose(lo, hi, abs_tol=1e-9):
        return f"(no interval: all {count} fixtures have the same value)"
    fmt = "+.2f" if sign else ".2f"
    note = ", clamped to the possible range" if clamped else ""
    return f"[{lo:{fmt}}, {hi:{fmt}}] (95% t over {count} fixtures{note})"


def print_summary(summary):
    """Print the human-readable report for a summary payload."""
    overall = summary["overall"]
    reps = summary["repeats"]
    for arm in summary["arms"]:
        o = overall[arm]
        lo, hi = o["ci95"]
        count = sum(1 for v in summary["fixtures"].values() if v[arm]["n"])
        print(f"overall {arm}: {o['pass']}/{o['n']} = {o['rate']:.2f} "
              f"({reps} rep(s) x {overall['n_fixtures']} fixtures), "
              f"mean fixture rate {o.get('fixture_mean', o['rate']):.2f} "
              f"{interval_text(lo, hi, count, sign=False, clamped=o.get('ci95_clamped', False))}")
    if "paired_mean_diff" in overall:
        lo, hi = overall["paired_ci95"]
        print(f"paired mean diff (progressive minus always-on): "
              f"{overall['paired_mean_diff']:+.2f} "
              f"{interval_text(lo, hi, overall['n_fixtures'], clamped=overall.get('paired_ci95_clamped', False))}")
        print("per-fixture progressive minus always-on:")
        for name in sorted(summary["fixtures"]):
            entry = summary["fixtures"][name]
            a, p = entry["always-on"], entry["progressive"]
            dlo, dhi = entry["diff_ci95"]
            print(f"  {name}: always-on {a['pass']}/{a['n']}, progressive "
                  f"{p['pass']}/{p['n']}, "
                  f"diff {entry['diff_progressive_minus_always_on']:+.2f} "
                  f"[{dlo:+.2f}, {dhi:+.2f}]")


def load_summary(path):
    """Read a summary.json payload; raise ValueError if it is not one."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not (isinstance(data, dict) and isinstance(data.get("fixtures"), dict)
            and isinstance(data.get("arms"), list)):
        raise ValueError(f"{path} is not a run_skill.py summary.json")
    return data


def print_baseline_diff(summary, baseline):
    """Print per-fixture pass-rate changes against a saved summary.

    Each fixture's change carries a Newcombe 95% interval, so a one-repeat
    wobble does not read as a regression. The overall line is the mean of
    the per-fixture changes with a t interval over fixtures. Settings that
    make two runs incomparable (model, judge, repeats, split) are printed as
    warnings first; a different skill version prints as a note.
    """
    print(f"against baseline: {baseline.get('model')}, skill "
          f"{baseline.get('skill_version')} at {baseline.get('commit')}, "
          f"{baseline.get('date')}")
    for key in ("model", "judge_model", "repeats", "split"):
        if summary.get(key) != baseline.get(key):
            print(f"  WARN {key} differs: baseline {baseline.get(key)!r}, "
                  f"this run {summary.get(key)!r}")
    # A release bumps the version without a skill change, and a skill change
    # lands before the release, so a version gap is a note, not a warning.
    if summary.get("skill_version") != baseline.get("skill_version"):
        print(f"  note: baseline is skill {baseline.get('skill_version')}, "
              f"this run is skill {summary.get('skill_version')}")
    if baseline.get("dirty"):
        print(f"  WARN the baseline was recorded with uncommitted changes, "
              f"so commit {baseline.get('commit')} may not hold its text")
    arms = [a for a in summary["arms"] if a in baseline["arms"]]
    if not arms:
        print(f"  no arm in common (baseline: {', '.join(baseline['arms'])})")
        return
    for arm in arms:
        print(f"{arm}, this run minus baseline:")
        names = sorted(set(summary["fixtures"]) | set(baseline["fixtures"]))
        totals = [0, 0, 0, 0]  # new pass, new n, old pass, old n
        diffs = []  # one rate change per shared fixture
        for name in names:
            new = summary["fixtures"].get(name, {}).get(arm)
            old = baseline["fixtures"].get(name, {}).get(arm)
            if new is None or old is None:
                print(f"  {name}: only in "
                      f"{'this run' if old is None else 'baseline'}")
                continue
            for i, v in enumerate((new["pass"], new["n"],
                                   old["pass"], old["n"])):
                totals[i] += v
            if new["n"] and old["n"]:
                diffs.append(new["pass"] / new["n"] - old["pass"] / old["n"])
            lo, hi = newcombe_diff_interval(new["pass"], new["n"],
                                            old["pass"], old["n"])
            print(f"  {name}: {old['pass']}/{old['n']} -> "
                  f"{new['pass']}/{new['n']}, "
                  f"diff {new['rate'] - old['rate']:+.2f} "
                  f"[{lo:+.2f}, {hi:+.2f}]")
        # Overall covers shared fixtures only: a fixture added since the
        # baseline would otherwise move the total without any change. The
        # change is the mean of per-fixture rate changes with a t interval,
        # not a Newcombe interval over pooled runs: repeats of one fixture
        # are correlated, so pooling them overstates the sample (issue #72).
        new_pass, new_n, old_pass, old_n = totals
        if diffs:
            avg, lo, hi = paired_mean_diff_interval(diffs)
            lo, hi, clamped = clamp_interval(lo, hi, -1.0, 1.0)
            print(f"  overall, shared fixtures: {old_pass}/{old_n} -> "
                  f"{new_pass}/{new_n}, mean change {avg:+.2f} "
                  f"{interval_text(lo, hi, len(diffs), clamped=clamped)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--judge-model", default=None,
                        help="model for the added-claims check (default: claude-opus-5)")
    parser.add_argument("--no-judge", action="store_true",
                        help="skip the added-claims check")
    parser.add_argument("--no-skill", action="store_true",
                        help="baseline: send the brief with no skill loaded")
    parser.add_argument("--arm", default="always-on",
                        choices=["always-on", "progressive", "both"],
                        help="which skill-loading arm to run "
                        "(default: always-on)")
    parser.add_argument("--repeats", type=int, default=1,
                        help="independent rewrites per fixture per arm "
                        "(default: 1; use 5 or more to size a skill change)")
    parser.add_argument("--split", default="all",
                        choices=["all", "dev", "heldout"],
                        help="which evals/splits.json fixture set to run "
                        "(default: all)")
    parser.add_argument("--out", default=str(ROOT / "evals" / "outputs"))
    parser.add_argument("--judge-only", metavar="DIR",
                        help="only re-run the claim check on rewrites saved in DIR")
    parser.add_argument("--baseline", metavar="SUMMARY",
                        help="print per-fixture changes against a saved "
                        "summary.json, such as evals/baselines/*.json")
    parser.add_argument("--compare-summary", metavar="SUMMARY",
                        help="with --baseline: compare this saved summary "
                        "instead of generating a new run")
    parser.add_argument("fixtures", nargs="*", help="fixture names (default: all)")
    args = parser.parse_args()

    baseline = None
    if args.baseline:
        try:
            baseline = load_summary(args.baseline)
        except (OSError, ValueError) as exc:
            print(f"FAIL (cannot read baseline: {exc})")
            return 2
    if args.compare_summary:
        if baseline is None:
            print("--compare-summary needs --baseline")
            return 2
        try:
            summary = load_summary(args.compare_summary)
        except (OSError, ValueError) as exc:
            print(f"FAIL (cannot read summary: {exc})")
            return 2
        print_baseline_diff(summary, baseline)
        return 0

    fixtures = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())

    try:
        split_names = load_split(args.split)
    except ValueError as exc:
        print(f"FAIL ({exc})")
        return 2
    if split_names is not None:
        wanted = set(split_names)
        unknown = wanted - {f.name for f in fixtures}
        if unknown:
            print(f"FAIL split {args.split!r} lists unknown fixtures: "
                  f"{', '.join(sorted(unknown))}")
            return 2
        fixtures = [f for f in fixtures if f.name in wanted]
        if not fixtures:
            print(f"FAIL split {args.split!r} selected no fixtures")
            return 2

    if args.fixtures:
        fixtures = [f for f in fixtures if f.name in args.fixtures]
        missing = set(args.fixtures) - {f.name for f in fixtures}
        if missing:
            on_disk = {p.name for p in FIXTURES_DIR.iterdir() if p.is_dir()}
            outside = sorted(n for n in missing if n in on_disk)
            unknown = sorted(n for n in missing if n not in on_disk)
            if outside:
                print(f"fixtures not in split {args.split!r}: "
                      f"{', '.join(outside)}")
            if unknown:
                print(f"unknown fixtures: {', '.join(unknown)}")
            return 2
    elif split_names is not None:
        print(f"split {args.split!r}: running {len(fixtures)} fixture(s)")

    if args.repeats < 1:
        print("--repeats must be >= 1")
        return 2
    if args.no_skill and args.arm != "always-on":
        print("--no-skill runs the unskilled baseline only; "
              "it cannot combine with --arm")
        return 2

    judge_model = args.judge_model or DEFAULT_JUDGE_MODEL
    if args.judge_only:
        # Read-and-judge only: never create or touch the --out directory.
        return judge_only(judge_model, Path(args.judge_only), fixtures)

    # Absolute, because the progressive arm runs `claude` with its cwd in the
    # staging dir: a relative --out would point --system-prompt-file there.
    out_dir = Path(args.out).resolve()
    # Before anything is written, so the record describes what the run reads.
    metadata = run_metadata(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.no_skill:
        arm_configs = [("baseline", BASELINE_HEADER, "", None)]
    else:
        # The progressive arm reads from a staging dir holding only the
        # skill, never the repo root: with the Read tool enabled, a repo
        # cwd would expose the grading rubric (checks.json, examples/).
        stage = None
        if args.arm in ("progressive", "both"):
            try:
                stage = str(stage_skill_root(out_dir))
            except OSError as exc:
                print(f"FAIL (cannot stage skill root in {out_dir}: {exc})")
                return 2
        progressive_cfg = ("progressive",
                           build_system_prompt(True, "progressive"),
                           "Read", stage)
        if args.arm == "both":
            arm_configs = [
                ("always-on", build_system_prompt(True, "always-on"), "", None),
                progressive_cfg,
            ]
        elif args.arm == "progressive":
            arm_configs = [progressive_cfg]
        else:
            arm_configs = [("always-on", build_system_prompt(True, "always-on"),
                            "", None)]
    arms = [label for label, _, _, _ in arm_configs]

    print(f"model: {args.model}" + ("" if args.no_judge else f", judge: {judge_model}")
          + (", no skill loaded (baseline)" if args.no_skill else "")
          + f", arm(s): {', '.join(arms)}"
          + f", repeats: {args.repeats}, split: {args.split}")

    # Flat legacy layout only for the historical default: one always-on (or
    # baseline) pass with a single repeat. Anything else gets one
    # subdirectory per arm so runs stay comparable and re-runnable.
    legacy = len(arm_configs) == 1 and args.repeats == 1
    results = {}
    all_ok = True
    for label, system_text, tools, cwd in arm_configs:
        arm_dir = out_dir if legacy else out_dir / label
        arm_dir.mkdir(parents=True, exist_ok=True)
        system_path = arm_dir / "_system_prompt.md"
        system_path.write_text(system_text, encoding="utf-8")
        for fixture_dir in fixtures:
            rep_paths = []
            for rep in range(1, args.repeats + 1):
                multi = len(arm_configs) > 1 or args.repeats > 1
                tag = f" [{label} r{rep}/{args.repeats}]" if multi else ""
                if legacy:
                    rewrite_path = arm_dir / f"{fixture_dir.name}.md"
                    claims_path = arm_dir / f"{fixture_dir.name}.claims.json"
                else:
                    rewrite_path = arm_dir / f"{fixture_dir.name}.r{rep}.md"
                    claims_path = (arm_dir
                                   / f"{fixture_dir.name}.r{rep}.claims.json")
                rep_paths.append((rewrite_path, claims_path))
                ok = generate_and_score(
                    args.model, judge_model, system_path, tools, cwd,
                    fixture_dir, rewrite_path, claims_path, args.no_judge,
                    tag=tag)
                results.setdefault(fixture_dir.name, {}).setdefault(
                    label, []).append(ok)
                all_ok &= ok
            if not legacy:
                # Copy the first repeat to the legacy names so run_evals.py
                # --all and compare_outputs.py work on each arm directory
                # unchanged.
                first_rewrite, first_claims = rep_paths[0]
                compat_rewrite = arm_dir / f"{fixture_dir.name}.md"
                compat_claims = arm_dir / f"{fixture_dir.name}.claims.json"
                try:
                    if first_rewrite.exists():
                        compat_rewrite.write_bytes(
                            first_rewrite.read_bytes())
                    else:
                        compat_rewrite.unlink(missing_ok=True)
                    if first_claims.exists():
                        compat_claims.write_bytes(first_claims.read_bytes())
                    else:
                        compat_claims.unlink(missing_ok=True)
                except OSError as exc:
                    print(f"  WARN could not write compat copy: {exc}")

    summary = build_summary(args.model, judge_model, args.no_judge, arms,
                            args.repeats, args.split, results, metadata)
    summary_path = out_dir / "summary.json"
    try:
        summary_path.write_text(json.dumps(summary, indent=2) + "\n",
                                encoding="utf-8")
    except OSError as exc:
        print(f"WARN could not write {summary_path}: {exc}")
    else:
        print(f"summary saved in {summary_path}")
    print_summary(summary)
    if baseline is not None:
        print_baseline_diff(summary, baseline)
    # Last, so the warnings do not scroll away above the report. The run
    # reads fixtures as it goes, so check the checkout again at the end.
    branch, on_branch = commit_on_default_branch(metadata.get("commit"))
    end = run_metadata(out_dir)
    for warning in reference_warnings(summary, branch, on_branch, end):
        print(f"WARN {warning}")

    print(f"rewrites saved in {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
