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
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_evals import FIXTURES_DIR, load_fixture  # noqa: E402

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


def ask(model, prompt):
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model, "--tools", "",
         "--output-format", "text"],
        capture_output=True, text=True, check=True)
    reply = result.stdout.strip()
    return reply[:1] if reply[:1] in "12" else None


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
        fixtures = [f for f in fixtures if f.name in args.fixtures]

    print(f"judge: {args.model}, A = {dir_a}, B = {dir_b}")
    tally = {"A": 0, "B": 0, "tie": 0}
    for fixture_dir in fixtures:
        path_a, path_b = dir_a / f"{fixture_dir.name}.md", dir_b / f"{fixture_dir.name}.md"
        if not (path_a.exists() and path_b.exists()):
            print(f"{fixture_dir.name}: skipped (missing rewrite)")
            continue
        checks, source = load_fixture(fixture_dir)
        text_a, text_b = path_a.read_text(encoding="utf-8"), path_b.read_text(encoding="utf-8")
        common = dict(brief=checks["brief"], source=source)
        first = ask(args.model, PROMPT.format(first=text_a, second=text_b, **common))
        second = ask(args.model, PROMPT.format(first=text_b, second=text_a, **common))
        if first == "1" and second == "2":
            verdict = "A"
        elif first == "2" and second == "1":
            verdict = "B"
        else:
            verdict = "tie"
        tally[verdict] += 1
        print(f"{fixture_dir.name}: {verdict} (orders: {first or '?'}, {second or '?'})")

    print(f"A wins {tally['A']}, B wins {tally['B']}, ties {tally['tie']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
