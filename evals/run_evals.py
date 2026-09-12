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

KNOWN_MARKERS = {
    "contraction_rate",
    "first_person_rate",
    "hedge_rate",
    "mean_word_length",
}


def normalize_apos(text):
    """Map curly apostrophes to ASCII so checks are punctuation-insensitive."""
    return text.replace("’", "'").replace("‘", "'").replace("ʼ", "'")


# Flexible separator for phrase matching: spaces, hyphens, dashes, newlines,
# and underscores are equivalent ("stand-up" matches "stand up", "Reports tab"
# matches "Reports-tab"). Used to build word-boundary regexes from checks.json
# phrases so hyphens/dashes/whitespace and surrounding punctuation do not
# matter, while partial-word matches ("37" in "137", "may" in "maybe",
# "Certainly" in "uncertainly", "clearly", "proves") still fail.
FLEX_SEP = r"[\s\-—–―−‐‑_]+"


def phrase_pattern(phrase, inflect=False):
    """Build a word-boundary regex for a required/banned phrase.

    Returns None for phrases with no alphanumeric characters (emoji, lone
    punctuation), where substring matching is correct.

    With inflect=True (required facts), a trailing inflection
    (s/es/ed/ing/d) is allowed so "sync" matches "syncs" while "may" still
    does not match "maybe" and "37" does not match "137".
    """
    norm = normalize_apos(phrase)
    if not re.search(r"[A-Za-z0-9]", norm):
        return None
    parts = [p for p in re.split(FLEX_SEP, norm) if p]
    if not parts:
        return None
    inner_pieces = []
    for part in parts:
        inner_pieces.append("".join(re.escape(ch) for ch in part))
    inner = FLEX_SEP.join(inner_pieces)
    first = parts[0][0]
    last = parts[-1][-1]
    if first.isdigit():
        left = r"(?<!\d)"
    elif first.isalnum() or first == "_":
        left = r"(?<!\w)"
    else:
        left = ""
    if last.isdigit():
        right = r"(?!\d)"
    elif last.isalnum() or last == "_":
        if inflect:
            inner = inner + r"(?:s|es|ed|ing|d)?"
        right = r"(?!\w)"
    else:
        right = ""
    return left + inner + right


def phrase_found(phrase, text, inflect=False):
    """Case-insensitive word-boundary search for a checks.json phrase."""
    norm_text = normalize_apos(text)
    pattern = phrase_pattern(phrase, inflect=inflect)
    if pattern is None:
        return normalize_apos(phrase).lower() in norm_text.lower()
    try:
        return re.search(pattern, norm_text, re.I) is not None
    except re.error:
        return normalize_apos(phrase).lower() in norm_text.lower()


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
# Patterns run case-insensitively on apostrophe- and whitespace-normalized
# text, allow newlines and cross-sentence spans, and cover was/were and
# it's/it-is variants.
CONTRAST = [
    (r"\bnot\s+(?:just|only|merely|simply)\b[\s\S]{0,120}?\bbut\b",
     "no 'not just X but Y' scaffold"),
    (r"\b(?:isn['’]?t|is not|wasn['’]?t|was not|weren['’]?t|were not|"
     r"aren['’]?t|are not|it['’]?s not|it is not)\s+"
     r"(?:just|only|merely|simply)\b",
     "no 'isn't just X' scaffold"),
    (r"\bit(?:['’]?s| is)\s+not\b[\s\S]{0,120}?\b(?:it(?:['’]?s| is)|but)\b",
     "no 'it's not X, it's Y' scaffold"),
    (r"\bnot\s+because\b[\s\S]{0,120}?\b(?:but\b(?:\s+because)?|because\b)",
     "no 'not because X but Y' scaffold"),
]

# Voice markers a rewrite moves even when told to keep the writer's voice
# (van Nuenen, "Voice Under Revision", 2026): contractions, first person, and
# hedges fall, mean word length rises. Each is measured per 100 words on the
# input and the rewrite; checks.json's "voice_drift" gives the largest change
# allowed per marker.
# WORD includes leading digits so counts ("37C", "3:30", "v2.4.0") do not skew
# the per-100 denominator. A possessive "'s" still counts as a contraction;
# only the input-to-rewrite change matters, so the skew cancels out.
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’-]*")
CONTRACTION = re.compile(r"\b\w+(?:n['’]t|['’](?:s|re|ve|ll|d|m))\b", re.I)
FIRST_PERSON = re.compile(
    r"\b(?:I|me|my|mine|myself|we|us|our|ours|ourselves)\b", re.I)
HEDGE = re.compile(
    r"\b(?:I think|I suspect|I guess|probably|perhaps|maybe|sort of|kind of|"
    r"seems|seemed|apparently|arguably|roughly|might|may|"
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
    # Normalize curly apostrophes before every check so "isn’t" matches
    # "isn't" in banned phrases, banned_regex, and CONTRAST.
    norm_rewrite = normalize_apos(rewrite_text)
    norm_input = normalize_apos(input_text)

    for field in ("required", "banned", "banned_regex"):
        val = checks.get(field, [])
        if field in checks and not isinstance(val, list):
            results.append((False, f"{field} must be a list, got "
                                   f"{type(val).__name__}"))
    required = checks.get("required", [])
    banned = checks.get("banned", [])
    banned_regex = checks.get("banned_regex", [])
    if not isinstance(required, list):
        required = []
    if not isinstance(banned, list):
        banned = []
    if not isinstance(banned_regex, list):
        banned_regex = []

    for fact in required:
        if not isinstance(fact, str):
            results.append((False, f"required fact must be a string, got "
                                   f"{fact!r}"))
            continue
        ok = phrase_found(fact, norm_rewrite, inflect=True)
        results.append((ok, f'required fact present: "{fact}"'))

    for phrase in banned:
        if not isinstance(phrase, str):
            results.append((False, f"banned phrase must be a string, got "
                                   f"{phrase!r}"))
            continue
        ok = not phrase_found(phrase, norm_rewrite, inflect=False)
        results.append((ok, f'banned phrase absent: "{phrase}"'))

    for pattern in banned_regex:
        if not isinstance(pattern, str):
            results.append((False, f"banned pattern must be a string, got "
                                   f"{pattern!r}"))
            continue
        try:
            ok = re.search(pattern, norm_rewrite, re.I) is None
        except re.error as exc:
            results.append((False, f"banned pattern invalid: /{pattern}/ ({exc})"))
            continue
        results.append((ok, f"banned pattern absent: /{pattern}/"))

    for pattern, desc in WELL_FORMED:
        ok = re.search(pattern, norm_rewrite) is None
        results.append((ok, f"well formed: {desc}"))

    # Collapse newlines/whitespace for structure checks so scaffolds split
    # across lines or sentences still match.
    contrast_text = re.sub(r"\s+", " ", norm_rewrite)
    for pattern, desc in CONTRAST:
        try:
            ok = re.search(pattern, contrast_text, re.I) is None
        except re.error as exc:
            results.append((False, f"structure pattern invalid: {desc} ({exc})"))
            continue
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
        if not isinstance(drift, dict):
            results.append((False, f"voice_drift must be an object, got "
                                   f"{type(drift).__name__}"))
        else:
            try:
                before = voice_metrics(norm_input)
                after = voice_metrics(norm_rewrite)
            except Exception as exc:
                results.append((False, f"voice metrics failed: {exc}"))
            else:
                for name, limit in drift.items():
                    if name not in KNOWN_MARKERS:
                        results.append((False, f"voice kept: unknown marker "
                                               f'"{name}" (known: '
                                               f"{', '.join(sorted(KNOWN_MARKERS))})"))
                        continue
                    if not isinstance(limit, (int, float)) or isinstance(limit, bool):
                        results.append((False, f"voice kept: limit for {name} "
                                               f"must be a number, got {limit!r}"))
                        continue
                    try:
                        delta = after[name] - before[name]
                    except KeyError:
                        results.append((False, f"voice kept: unknown marker "
                                               f'"{name}"'))
                        continue
                    results.append((abs(delta) <= limit,
                                    f"voice kept: {name} {before[name]:.1f} -> {after[name]:.1f} "
                                    f"(change {delta:+.1f}, limit {limit})"))

    return results


def run_one(fixture_dir, rewrite_path):
    try:
        checks, input_text = load_fixture(fixture_dir)
        rewrite_text = Path(rewrite_path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"{Path(fixture_dir).name}: FAIL (bad fixture or rewrite: {exc})")
        return False
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"{Path(fixture_dir).name}: FAIL (bad fixture JSON: {exc})")
        return False
    except KeyError as exc:
        print(f"{Path(fixture_dir).name}: FAIL (bad fixture: missing {exc})")
        return False
    try:
        results = check_rewrite(checks, input_text, rewrite_text)
    except (KeyError, TypeError, ValueError) as exc:
        print(f"{Path(fixture_dir).name}: FAIL (bad fixture: {exc})")
        return False

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
        try:
            fixtures = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())
        except OSError as exc:
            print(f"FAIL (cannot list fixtures in {FIXTURES_DIR}: {exc})")
            return 2
        if not fixtures:
            print(f"no fixtures found in {FIXTURES_DIR}")
            return 2
        for fixture_dir in fixtures:
            rewrite_path = outputs_dir / f"{fixture_dir.name}.md"
            if not rewrite_path.exists():
                print(f"{fixture_dir.name}: FAIL (no rewrite at {rewrite_path})")
                all_ok = False
                continue
            try:
                ok = run_one(fixture_dir, rewrite_path)
            except (OSError, ValueError, KeyError) as exc:
                # json.JSONDecodeError subclasses ValueError.
                print(f"{fixture_dir.name}: FAIL (bad fixture: {exc})")
                ok = False
            except re.error as exc:
                print(f"{fixture_dir.name}: FAIL (bad pattern: {exc})")
                ok = False
            all_ok &= ok
        return 0 if all_ok else 1

    try:
        return 0 if run_one(argv[1], argv[2]) else 1
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL (bad fixture or rewrite: {exc})")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
