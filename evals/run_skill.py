#!/usr/bin/env python3
"""Run the skill on every fixture with a real model, then check the rewrites.

Usage:
    python3 evals/run_skill.py [--model MODEL] [--out DIR] [fixture-name ...]

Each fixture's input.md is sent to `claude -p` with SKILL.md and every file in
references/ as the system prompt and the fixture's brief as the instruction.
Rewrites land in DIR (default evals/outputs/) as <fixture-name>.md, then
run_evals.py checks them. Exits non-zero if any fixture fails.

Requires the Claude Code CLI (`claude`) on PATH with working credentials.
The model is claude-opus-5 unless --model says otherwise.
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_evals import FIXTURES_DIR, load_fixture, run_one  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

SYSTEM_HEADER = """You are running the better-writing skill. Its instructions and reference
material follow. Apply them to the user's request.

Output rules for this run: return only the final rewritten text. No preamble,
no change note, no diagnostic audit, no closing remark.
"""


def build_system_prompt():
    parts = [SYSTEM_HEADER, (ROOT / "SKILL.md").read_text(encoding="utf-8")]
    for ref in sorted((ROOT / "references").glob("*.md")):
        parts.append(f"\n\n<!-- references/{ref.name} -->\n\n" + ref.read_text(encoding="utf-8"))
    return "\n".join(parts)


def rewrite(model, system_path, brief, input_text):
    prompt = f"{brief}\n\nText:\n\n{input_text}"
    result = subprocess.run(
        ["claude", "-p", prompt,
         "--model", model,
         "--system-prompt-file", str(system_path),
         "--tools", "",
         "--output-format", "text"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", default="claude-opus-5")
    parser.add_argument("--out", default=str(ROOT / "evals" / "outputs"))
    parser.add_argument("fixtures", nargs="*", help="fixture names (default: all)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    system_path = out_dir / "_system_prompt.md"
    system_path.write_text(build_system_prompt(), encoding="utf-8")

    fixtures = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())
    if args.fixtures:
        fixtures = [f for f in fixtures if f.name in args.fixtures]
        missing = set(args.fixtures) - {f.name for f in fixtures}
        if missing:
            print(f"unknown fixtures: {', '.join(sorted(missing))}")
            return 2

    all_ok = True
    for fixture_dir in fixtures:
        checks, input_text = load_fixture(fixture_dir)
        try:
            text = rewrite(args.model, system_path, checks["brief"], input_text)
        except subprocess.CalledProcessError as exc:
            print(f"{fixture_dir.name}: FAIL (claude exited {exc.returncode})")
            print(exc.stderr.strip())
            all_ok = False
            continue
        rewrite_path = out_dir / f"{fixture_dir.name}.md"
        rewrite_path.write_text(text, encoding="utf-8")
        all_ok &= run_one(fixture_dir, rewrite_path)

    print(f"rewrites saved in {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
