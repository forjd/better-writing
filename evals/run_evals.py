#!/usr/bin/env python3
"""Check a rewrite against a fixture's preservation and anti-slop rules.

Usage:
    python3 evals/run_evals.py <fixture-dir> <rewrite-file>
    python3 evals/run_evals.py --all <outputs-dir>

In --all mode, <outputs-dir> must contain one file per fixture, named
<fixture-name>.md (for example outputs/launch-email.md). Exits non-zero
if any check fails. No dependencies beyond the standard library.
"""

import json
import re
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(fixture_dir):
    fixture_dir = Path(fixture_dir)
    checks = json.loads((fixture_dir / "checks.json").read_text(encoding="utf-8"))
    input_text = (fixture_dir / "input.md").read_text(encoding="utf-8")
    return checks, input_text


def word_count(text):
    return len(text.split())


def check_rewrite(checks, input_text, rewrite_text):
    """Return a list of (passed, description) tuples."""
    results = []
    lower = rewrite_text.lower()

    for fact in checks.get("required", []):
        ok = fact.lower() in lower
        results.append((ok, f'required fact present: "{fact}"'))

    for phrase in checks.get("banned", []):
        ok = phrase.lower() not in lower
        results.append((ok, f'banned phrase absent: "{phrase}"'))

    for pattern in checks.get("banned_regex", []):
        ok = re.search(pattern, rewrite_text) is None
        results.append((ok, f"banned pattern absent: /{pattern}/"))

    max_ratio = checks.get("max_words_ratio")
    min_ratio = checks.get("min_words_ratio")
    if max_ratio is not None or min_ratio is not None:
        ratio = word_count(rewrite_text) / max(word_count(input_text), 1)
        if max_ratio is not None:
            results.append((ratio <= max_ratio,
                            f"length ratio {ratio:.2f} <= {max_ratio} (no padding)"))
        if min_ratio is not None:
            results.append((ratio >= min_ratio,
                            f"length ratio {ratio:.2f} >= {min_ratio} (no over-cutting)"))

    return results


def run_one(fixture_dir, rewrite_path):
    checks, input_text = load_fixture(fixture_dir)
    rewrite_text = Path(rewrite_path).read_text(encoding="utf-8")
    results = check_rewrite(checks, input_text, rewrite_text)

    name = checks.get("name", Path(fixture_dir).name)
    failures = [desc for ok, desc in results if not ok]
    print(f"{name}: {len(results) - len(failures)}/{len(results)} checks passed")
    for desc in failures:
        print(f"  FAIL {desc}")
    return not failures


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip())
        return 2

    if argv[1] == "--all":
        outputs_dir = Path(argv[2])
        all_ok = True
        fixtures = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())
        if not fixtures:
            print(f"no fixtures found in {FIXTURES_DIR}")
            return 2
        for fixture_dir in fixtures:
            rewrite_path = outputs_dir / f"{fixture_dir.name}.md"
            if not rewrite_path.exists():
                print(f"{fixture_dir.name}: FAIL (no rewrite at {rewrite_path})")
                all_ok = False
                continue
            all_ok &= run_one(fixture_dir, rewrite_path)
        return 0 if all_ok else 1

    return 0 if run_one(argv[1], argv[2]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
