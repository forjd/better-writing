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


# Damage a search-and-replace rewrite leaves behind: doubled spaces mid-line,
# a space before closing punctuation, or two punctuation marks with nothing
# between them ("I !", "our  new", "to .", "update ,.").
WELL_FORMED = [
    (r"\S[^\S\n]{2,}\S", "no doubled spaces inside a line"),
    (r"\s[,.;:!?]", "no space before punctuation"),
    (r"[,;:!?]\s*[,;:!?]", "no empty clause between punctuation marks"),
]


# Binary-contrast scaffolds, the structure sam-paech's slop-score weights at a
# quarter of its total and 2026 reporting puts at three times the human rate.
# Checked on every rewrite; no fixture's ideal output needs one.
CONTRAST = [
    (r"\bnot (?:just|only|merely|simply)\b[^.?!\n]{0,80}\bbut\b",
     "no 'not just X but Y' scaffold"),
    (r"\b(?:isn'?t|is not|wasn'?t|aren'?t|are not)\s+(?:just|only|merely|simply)\b",
     "no 'isn't just X' scaffold"),
    (r"\bit'?s not (?:about|that)\b[^.?!\n]{0,80}\b(?:it'?s|but)\b",
     "no 'it's not about X, it's Y' scaffold"),
    (r"\bnot because\b[^.?!\n]{0,80}\b(?:but )?because\b",
     "no 'not because X but because Y' scaffold"),
]

# Voice markers a rewrite moves even when told to keep the writer's voice
# (van Nuenen, "Voice Under Revision", 2026): contractions, first person, and
# hedges fall, mean word length rises. Each is measured per 100 words on the
# input and the rewrite; checks.json's "voice_drift" gives the largest change
# allowed per marker.
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
CONTRACTION = re.compile(r"\b\w+(?:n['’]t|['’](?:s|re|ve|ll|d|m))\b", re.I)
FIRST_PERSON = re.compile(r"\b(?:I|me|my|mine|myself|we|us|our|ours)\b")
HEDGE = re.compile(
    r"\b(?:I think|I suspect|I guess|probably|perhaps|maybe|sort of|kind of|"
    r"seems|seemed|apparently|arguably|roughly|about|around|might|may|"
    r"tends? to|not sure)\b", re.I)


def voice_metrics(text):
    words = WORD.findall(text)
    n = max(len(words), 1)
    per_100 = 100.0 / n
    return {
        "contraction_rate": len(CONTRACTION.findall(text)) * per_100,
        "first_person_rate": len(FIRST_PERSON.findall(text)) * per_100,
        "hedge_rate": len(HEDGE.findall(text)) * per_100,
        "mean_word_length": sum(len(w) for w in words) / n,
    }


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

    for pattern, desc in WELL_FORMED:
        ok = re.search(pattern, rewrite_text) is None
        results.append((ok, f"well formed: {desc}"))

    for pattern, desc in CONTRAST:
        ok = re.search(pattern, rewrite_text, re.I) is None
        results.append((ok, f"structure: {desc}"))

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

    drift = checks.get("voice_drift")
    if drift:
        before = voice_metrics(input_text)
        after = voice_metrics(rewrite_text)
        for name, limit in drift.items():
            delta = after[name] - before[name]
            results.append((abs(delta) <= limit,
                            f"voice kept: {name} {before[name]:.1f} -> {after[name]:.1f} "
                            f"(change {delta:+.1f}, limit {limit})"))

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
