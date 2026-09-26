#!/usr/bin/env python3
"""Lint the repo's own prose against the skill's own audit. Dependency-free.

Scope: README.md, SKILL.md and CHANGELOG.md at the repo root. references/
is deliberately out of scope: it IS the tell catalogue, so scanning it for
tells is meaningless. Run from anywhere; exits non-zero on any violation.

Exclusions (each measured and reported below, so a dead exclusion shows up
as a zero in the report rather than rotting silently):

- fenced code blocks (``` ... ```): install commands and usage transcripts
- blockquote lines (> ...): the before/after examples, including the
  intentionally bad "before" texts
- inline code spans (`...`): checker names, fixture fields, placeholder
  spellings such as `[Your Name]`
- double-quoted spans ("..." / "..."): mentions, not uses. The skill must
  name a tell to teach it ("some internal observers suggest" becomes ...),
  and a quoted tell is documentation, not voice.

Probes (every one fires zero times on the current docs after exclusions;
that zero is the regression baseline):

- near-conclusive artefacts from references/ai-writing-patterns.md: leaked
  tool markup, tracking parameters, unfilled placeholders, standalone model
  disclaimers and multi-word chatbot scaffolding. A single instance is hard
  evidence, so a single instance fails the lint.
- binary-contrast scaffolds, imported from evals/run_evals.py (single source
  of truth; the lint refuses to run its structure checks if its embedded
  copy drifts from the checker's). The full scaffold is required, never a
  bare "isn't just": bare-phrase matching is the false-positive class this
  lint exists to avoid (vale-ai-tells PR #49: a rule that passed fixtures
  reported 62 false positives on a real corpus, cut to 27 only by requiring
  the real conjunction).
- curated multi-word live slop: phrases that would be embarrassing in the
  repo's own voice (launch-email openers, jargon-table entries, engagement
  bait, rhetorical self-answers). Multi-word only, on purpose.

Intentionally out of scope, with reasons:

- single-word vocabulary (delve, seamless, robust, ...): the skill's own
  confidence tiers say a single instance is never a tell, so linting for one
  would flag the catalogue's own legacy list in CHANGELOG.md. Cluster
  detection across whole docs is future work, not this gate.
- invented-metric and broetry regexes from the checker: they fire on
  legitimate badges, headings and dated research figures in these docs.
- em/en dashes: a lone dash is the writer's choice and stays (SKILL.md),
  and a dash-free text proves nothing. Dashes are counted and reported as
  information only; numeric and date ranges are exempt from the count.
"""

import bisect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ["README.md", "SKILL.md", "CHANGELOG.md"]

sys.path.insert(0, str(ROOT / "evals"))
try:
    from run_evals import CONTRAST as CHECKER_CONTRAST
    from run_evals import normalize_apos, phrase_found, phrase_pattern
    IMPORT_ERROR = None
except ImportError as exc:  # evals/ missing (e.g. partial checkout)
    CHECKER_CONTRAST = None
    IMPORT_ERROR = str(exc)

# Embedded copy of the checker's binary-contrast scaffolds. Used only when
# the import above fails; when the import works the two must agree (checked
# in main) so the lint and the checker can never drift apart silently.
EMBEDDED_CONTRAST = [
    (r"\bnot\s+(?:just|only|merely|simply)\b[\s\S]{0,120}?\bbut\b",
     "no 'not just X but Y' scaffold"),
    (r"\b(?:isn['’]?t|is not|wasn['’]?t|was not|weren['’]?t|were not|"
     r"aren['’]?t|are not|it['’]?s not|it is not|doesn['’]?t|does not|"
     r"don['’]?t|do not|didn['’]?t|did not)\s+"
     r"(?:just|only|merely|simply)\b",
     "no 'isn't just X' scaffold"),
    (r"\bit(?:['’]?s| is)\s+not\b(?:[\s\S]{0,120}?\bit(?:['’]?s| is)\b|"
     r"[^.!?]{0,120}?\bbut\s+(?:a|an|about|rather|instead)\b)",
     "no 'it's not X, it's Y' scaffold"),
    (r"\bnot\s+because\b[\s\S]{0,120}?\b(?:but\b(?:\s+because)?|because\b)",
     "no 'not because X but Y' scaffold"),
    (r"\b(?:this|that|it)\s+(?:does not|doesn't|did not|didn't)\s+mean\b"
     r"[^.!?;]{0,120}[.!?;,\u2014\u2013]\s*(?:it|this|that)\s+(?:means|meant)\b",
     "no 'this doesn't mean X. It means Y' scaffold"),
    (r"\b(?:this|that|it)\s+(?:is not|isn't|was not|wasn't)\s+"
     r"(?:really\s+|just\s+)?about\b[^.!?;]{0,120}[.!?;,\u2014\u2013]\s*"
     r"(?:it|this|that)(?:'s|\s+is|\s+was)\s+(?:really\s+|just\s+)?about\b",
     "no 'this isn't about X. It's about Y' scaffold"),
]

# (phrase, skill section that bans it live). Multi-word only; see module note.
LIVE_SLOP = [
    ("hope this email finds you well", "Stock openers"),
    ("thrilled to announce", "Promotional language"),
    ("thrilled", "Promotional language"),
    ("groundbreaking", "Promotional language"),
    ("game-changer", "Business jargon"),
    ("transform your workflow", "Promotional language"),
    ("exciting journey", "Filler / closers"),
    ("exciting times lie ahead", "Filler / closers"),
    ("simply navigate", "Launch-email slop"),
    ("full potential", "Marketing copy"),
    ("has you covered", "Marketing copy"),
    ("leading the way", "Marketing copy"),
    ("future of work", "Stock openers"),
    ("supercharge", "Marketing and SEO"),
    ("exciting", "Promotional language"),
    ("important to note", "Filler, performed hedging"),
    ("worth noting", "Filler, performed hedging"),
    ("when it comes to", "Filler, performed hedging"),
    ("significant challenge", "Significance inflation"),
    ("competitive landscape", "Significance inflation"),
    ("implications are significant", "Empty importance"),
    ("the stakes are high", "Empty importance"),
    ("moving forward", "Business jargon"),
    ("circle back", "Business jargon"),
    ("on the same page", "Business jargon"),
    ("move the needle", "Business jargon"),
    ("low-hanging fruit", "Business jargon"),
    ("take it to the next level", "Business jargon"),
    ("deep dive", "Business jargon"),
    ("navigate challenges", "Business jargon"),
    ("I wanted to reach out", "Over-signposting fixture"),
    ("That being said", "Mechanical transitions"),
    ("In conclusion", "Essay-scaffold closers"),
    ("To summarise", "Essay-scaffold closers"),
    ("In summary", "Essay-scaffold closers"),
    ("At the end of the day", "Essay-scaffold closers"),
    ("It goes without saying", "Mechanical transitions"),
    ("Needless to say", "Mechanical transitions"),
    ("In essence", "Mechanical transitions"),
    ("Let that sink in", "Emphasis crutches"),
    ("Make no mistake", "Emphasis crutches"),
    ("Here's why that matters", "Emphasis crutches"),
    ("This matters because", "Emphasis crutches"),
    ("Read that again", "Dramatic fragmentation"),
    ("What if I told you", "Rhetorical setups"),
    ("I'm no expert, but", "Rhetorical setups"),
    ("This might be controversial, but", "Rhetorical setups"),
    ("The result?", "Rhetorical self-answer"),
    ("The kicker?", "Rhetorical self-answer"),
    ("The good news?", "Rhetorical self-answer"),
    ("Here's the kicker", "Meta-commentary joiners"),
    ("Plot twist", "Meta-commentary joiners"),
    ("Unpopular opinion", "Social-post tells"),
    ("currency of", "Aphorism formula"),
    ("productivity hack", "Social-post tells"),
    ("nobody has asked", "Added-claims judge"),
    ("nobody asked", "Added-claims judge"),
    ("That's where", "Engagement bait"),
    ("Not all", "Engagement bait"),
    ("are created equal", "Engagement bait"),
    ("Agree?", "Engagement bait"),
    ("Thoughts?", "Engagement bait"),
    ("at its core", "Filler, performed hedging"),
    ("the real question is", "Filler, performed hedging"),
    ("the future looks bright", "Filler, performed hedging"),
    ("in conclusion", "Essay-scaffold closers"),
    ("recieve", "Typo tripwire"),
    ("waitng", "Typo tripwire"),
    ("Rest assured", "Chatbot scaffolding"),
    ("Great question", "Sycophancy"),
    ("Happy to help", "Communication artefacts"),
    ("I'd be happy to", "Communication artefacts"),
    ("You're absolutely right", "Sycophancy"),
    ("That's a brilliant question", "Sycophancy"),
    ("What a thoughtful observation", "Sycophancy"),
    ("😊", "Decorative emoji"),
    ("🎉", "Decorative emoji"),
    ("👇", "Decorative emoji"),
]

# Near-conclusive artefacts: one instance in live prose fails the lint.
ARTEFACTS = [
    ("[Your Name]", "Unfilled placeholder (gap markers like [figure needed] stay)"),
    ("[Insert X here]", "Unfilled placeholder"),
    ("[Company]", "Unfilled placeholder"),
    ("[Date]", "Unfilled placeholder"),
    ("As an AI language model", "Standalone model disclaimer"),
    ("As a large language model", "Standalone model disclaimer"),
    ("I don't have access to real-time information", "Standalone disclaimer"),
    ("As of my last update", "Standalone disclaimer"),
    ("Let me know if you need any modifications", "Assistant scaffolding"),
    ("Here is the revised version", "Assistant scaffolding"),
    ("I hope this helps", "Assistant scaffolding"),
    ("Would you like me to", "Assistant scaffolding"),
    ("Let me break this down", "Assistant scaffolding"),
    ("Let me walk you through", "Assistant scaffolding"),
    ("Here is an overview", "Assistant scaffolding"),
    ("Claude responded:", "Pasted chat label"),
    ("oaicite", "Leaked citation markup"),
    ("oai_citation", "Leaked citation markup"),
    ("contentReference", "Leaked citation markup"),
    ("turn0search0", "Leaked citation markup"),
    ("citeturn", "Leaked citation markup"),
    ("attributableIndex", "Leaked citation markup"),
    (":::writing", "Leaked ChatGPT block"),
    ("Example+1", "Leaked source chip"),
    ("grok_card", "Leaked Grok markup"),
    ("grok_render_citation_card", "Leaked Grok markup"),
    ("<grok-card", "Leaked Grok markup"),
    ("[cite: 1]", "Leaked Gemini markup"),
    ("[web:1]", "Leaked Perplexity markup"),
    ("attached_file", "Leaked upload markup"),
    ("ppl-ai-file-upload", "Leaked upload markup"),
    ("utm_source=chatgpt.com", "Tracking parameter"),
    ("utm_source=openai", "Tracking parameter"),
    ("utm_source=copilot.com", "Tracking parameter"),
    ("referrer=grok.com", "Tracking parameter"),
    ("<thinking>", "Reasoning tag as text"),
]

LENTICULAR_RE = re.compile(r"【[^】]*†[^】]*】")
PUA_RE = re.compile(r"[\ue000-\uf8ff]")
ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
NUMERIC_RANGE_DASH_RE = re.compile(r"[\w\d][—–][\w\d]")


def strip_markdown(text):
    """Remove fences, blockquotes, inline code and quoted mentions.

    Returns (cleaned_text, raw_line_map, measurements). raw_line_map[i] is
    the 1-based raw line number of cleaned line i.
    """
    measurements = {
        "fence_lines": 0,
        "blockquote_lines": 0,
        "inline_code_spans": 0,
        "quoted_spans": 0,
    }
    kept = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            measurements["fence_lines"] += 1
            continue
        if in_fence:
            measurements["fence_lines"] += 1
            continue
        if line.lstrip().startswith(">"):
            measurements["blockquote_lines"] += 1
            continue
        kept.append((lineno, line))
    cleaned_lines = []
    raw_map = []
    for lineno, line in kept:
        line, n1 = re.subn(r"`[^`\n]*`", " ", line)
        measurements["inline_code_spans"] += n1
        line, n2 = re.subn(r'"[^"\n]*"|“[^”\n]*”', " ", line)
        measurements["quoted_spans"] += n2
        cleaned_lines.append(line)
        raw_map.append(lineno)
    return "\n".join(cleaned_lines), raw_map, measurements


def _line_offsets(text):
    offsets = [0]
    for match in re.finditer(r"\n", text):
        offsets.append(match.end())
    return offsets


def cleaned_offset_to_raw(offset, cleaned_text, raw_map):
    line_idx = bisect.bisect_right(_line_offsets(cleaned_text), offset) - 1
    line_idx = max(0, min(line_idx, len(raw_map) - 1))
    return raw_map[line_idx]


def check_phrases(cleaned_text, raw_map, phrases, label):
    """Return FAIL lines for phrase probes; empty list means clean."""
    failures = []
    norm = normalize_apos(cleaned_text)
    for phrase, reason in phrases:
        if not phrase_found(phrase, cleaned_text, inflect="banned"):
            continue
        pattern = phrase_pattern(phrase, inflect="banned")
        if pattern is None:
            idx = norm.lower().find(normalize_apos(phrase).lower())
            raw = cleaned_offset_to_raw(max(idx, 0), cleaned_text, raw_map)
        else:
            match = re.search(pattern, norm, re.I)
            raw = cleaned_offset_to_raw(match.start(), cleaned_text, raw_map) if match else "?"
        failures.append(f"{label} {phrase!r} ({reason}) at raw line {raw}")
    return failures


def check_contrast(cleaned_text, raw_map, contrast):
    failures = []
    # No whitespace collapsing: \s and [\s\S] in the patterns already span
    # newlines, so offsets map back to raw lines exactly.
    norm = normalize_apos(cleaned_text)
    for pattern, desc in contrast:
        try:
            match = re.search(pattern, norm, re.I)
        except re.error:
            failures.append(f"structure pattern invalid: {desc}")
            continue
        if match:
            raw = cleaned_offset_to_raw(match.start(), cleaned_text, raw_map)
            failures.append(f"structure {desc} at raw line {raw}")
    return failures


def check_invisible(cleaned_text, raw_map):
    failures = []
    for match in PUA_RE.finditer(cleaned_text):
        raw = cleaned_offset_to_raw(match.start(), cleaned_text, raw_map)
        failures.append(f"invisible private-use char U+{ord(match.group(0)):04X} at raw line {raw}")
    for match in LENTICULAR_RE.finditer(cleaned_text):
        raw = cleaned_offset_to_raw(match.start(), cleaned_text, raw_map)
        failures.append(f"lenticular-bracket citation at raw line {raw}")
    for match in ZERO_WIDTH_RE.finditer(cleaned_text):
        ch = match.group(0)
        # Legitimate carve-outs: joiner inside emoji sequences, BOM at byte 0.
        if ch == "\u200d" and re.match(
            r".(?:\U0001F000-\U0001FAFF|\u2600-\u27BF|\uFE0F)$",
            cleaned_text[max(0, match.start() - 2):match.start()],
        ):
            continue
        if ch == "\ufeff" and match.start() == 0:
            continue
        raw = cleaned_offset_to_raw(match.start(), cleaned_text, raw_map)
        failures.append(f"zero-width char U+{ord(ch):04X} at raw line {raw}")
    return failures


def dash_census(cleaned_text):
    """Count dashes outside numeric/date ranges. Information only."""
    exempt = set()
    for match in NUMERIC_RANGE_DASH_RE.finditer(cleaned_text):
        exempt.add(match.start() + 1)
    return sum(1 for m in re.finditer(r"[—–]", cleaned_text) if m.start() not in exempt)


def main():
    if CHECKER_CONTRAST is None:
        print(f"FAIL lint_prose: cannot import evals/run_evals ({IMPORT_ERROR})")
        return 2
    contrast = CHECKER_CONTRAST
    if [p for p, _ in contrast] != [p for p, _ in EMBEDDED_CONTRAST]:
        print("FAIL lint_prose: embedded contrast patterns drifted from "
              "evals/run_evals.py CONTRAST; sync them")
        return 1

    errors = []
    totals = {"fence_lines": 0, "blockquote_lines": 0,
              "inline_code_spans": 0, "quoted_spans": 0}
    naive_hits = 0
    dash_total = 0
    checked = 0
    for target in TARGETS:
        path = ROOT / target
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"FAIL {target}: unreadable ({exc})")
            continue
        checked += 1
        cleaned, raw_map, measurements = strip_markdown(raw)
        for key in totals:
            totals[key] += measurements[key]

        # Naive comparison: same probes on raw text, to prove the exclusions
        # are load-bearing rather than decorative.
        naive = 0
        for phrase, _ in ARTEFACTS + LIVE_SLOP:
            if phrase_found(phrase, raw, inflect="banned"):
                naive += 1
        flat_raw = re.sub(r"\s+", " ", normalize_apos(raw))
        for pattern, _ in contrast:
            try:
                if re.search(pattern, flat_raw, re.I):
                    naive += 1
            except re.error:
                pass
        naive_hits += naive

        file_errors = []
        file_errors += check_phrases(cleaned, raw_map, ARTEFACTS, "artefact")
        file_errors += check_phrases(cleaned, raw_map, LIVE_SLOP, "live slop")
        file_errors += check_contrast(cleaned, raw_map, contrast)
        file_errors += check_invisible(cleaned, raw_map)
        dash_total += dash_census(cleaned)
        for failure in file_errors:
            errors.append(f"FAIL {target}:{failure}")

    if errors:
        for message in errors:
            print(message)
        print(f"{len(errors)} prose violation(s) found")
        return 1
    print(f"prose lint passed: 0 violations in {checked} file(s) "
          f"(excluded {totals['fence_lines']} fence lines, "
          f"{totals['blockquote_lines']} blockquote lines, "
          f"{totals['inline_code_spans']} code spans, "
          f"{totals['quoted_spans']} quoted mentions; "
          f"naive scan without exclusions would report {naive_hits}; "
          f"dashes outside ranges: {dash_total}, info only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
