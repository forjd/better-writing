# Evals

Regression tests for the skill. Each fixture is a text seeded with known AI tells and known facts. A passing rewrite removes the tells and keeps the facts. The checker (run_evals.py) is dependency-free Python.

This directory is repo tooling. Agents using the skill do not load it.

## Workflow

Run every fixture through a real model with the skill loaded, then check the rewrites:

```bash
python3 evals/run_skill.py                       # all fixtures, claude-opus-5
python3 evals/run_skill.py --model claude-sonnet-5 launch-email plain-human
```

The runner builds a system prompt from `SKILL.md` plus every file in `references/`, sends each fixture's `input.md` with its `brief` through `claude -p` with no tools, saves the rewrite to `evals/outputs/<fixture-name>.md` (gitignored), and runs the checker on it. It needs the Claude Code CLI on PATH with working credentials. Run it before and after any change to `SKILL.md` or the pattern lists and compare the reports, and read the outputs, since a pass count says nothing about whether the prose reads well. The report's first line names the model, because length and formatting defaults differ between models.

After the checker, the runner makes a second model call that lists every claim in the rewrite that neither the input nor the brief states or implies: a next step, a line about what has happened since, an opinion, verdict, thanks, or joke the source lacks. It also lists claims whose strength changed on the way, such as a hope restated as something that has happened ("paving the way for a rollout" becoming "the rollout continues") or an emphasis restated as a cause. One listed claim fails the fixture, and the list is saved next to the rewrite as `<fixture-name>.claims.json`. This exists because the substring checker cannot see invention: a rewrite that added "nobody has asked to bring the stand-up back" to the LinkedIn fixture passed every substring check. Read a flagged claim before acting on it.

The judge sees the brief, so a fact the brief supplies ("the churn numbers are not available") is not listed. Its answer is the last JSON array of strings in the reply, since a judge sometimes answers, second-guesses itself, and answers again. A reply with no such array is asked once more, and if that fails too the fixture fails as a judge error, not as an invented claim.

Calibration, with `claude-opus-5` as judge, against saved outputs labelled by reading them: all 11 known-good examples pass, the 13 clean model rewrites pass (including one that restates a fact from the brief), and all 6 inventions are listed, including three hope-to-fact endings the previous prompt missed. The first pass also flagged three known-good examples, and each flag was right ("minor" performance improvements the source never sized, a verdict on one meeting the source only made about meetings in general, and hedges dropped from "may have contributed"), so those examples were corrected. To re-check the judge after changing its prompt, re-run it on saved rewrites without generating new ones:

```bash
python3 evals/run_skill.py --judge-only evals/outputs
```
 A smaller judge over-flags: `claude-sonnet-5` listed changes in attribution strength that the prompt tells it to ignore, so keep the judge on the default model. Pass `--no-judge` to skip the call and `--judge-model` to override it.

To check rewrites you produced some other way, save them as `<fixture-name>.md` and run the checker directly:

```bash
python3 evals/run_evals.py evals/fixtures/launch-email my-outputs/launch-email.md
python3 evals/run_evals.py --all my-outputs
```

The checker exits non-zero on any failure.

## Baseline and pairwise comparison

A pass count shows the skill removed what the fixtures ban. It does not show the skill did better than the model would have done unaided. To check that, produce a baseline with the same briefs and no skill loaded, then compare the two sets pairwise:

```bash
python3 evals/run_skill.py --no-skill --no-judge --out evals/baseline
python3 evals/run_skill.py
python3 evals/compare_outputs.py evals/baseline evals/outputs
```

The comparison shows the judge the brief, the source, and both rewrites, unlabelled and in both orders, and counts a win only when the same rewrite wins both ways. Judges prefer low-perplexity text and the first item shown, and they agree with human writing preferences only about three quarters of the time, so treat a loss as a flag to read both outputs, not a verdict. Never label which output came from the skill: labelled authorship shifts judge preference by tens of points.

## Why detector scores are not a check

Do not add an AI-detector score to this harness. Four reasons. First, the target is wrong: Pangram's own analysis of humaniser output found that the more readable and fluent the text, the more likely it is to be detected, so optimising against a detector rewards worse prose. Second, the signal is unstable: a 2026 study found light AI edits flagged between 38% and 80% of the time while unmodified human abstracts were flagged 9% to 15% of the time, and adversarial paraphrasing cuts detection by around 88%. Third, the bias is real: a 2026 ACL study across 16 detectors found essays by English language learners over-flagged, and non-white learners more so, and a 2025 benchmark found dialect, teen, and informal writing scored worst. Fourth, a detector cannot separate a human draft a model lightly polished from generated text, which is exactly the output this skill produces. The skill's stated goal is fit and clarity, and the false-positive fixtures exist to keep it from behaving like a detector in reverse.

## Human corpus

`human-corpus/` holds about 1,900 words of human prose written long before ChatGPT: a PEP, Strunk, Twain, and Jerome K. Jerome, all public domain, with provenance in its README. Run every check over it:

```bash
python3 evals/run_evals.py --corpus evals/human-corpus
```

The report lists each check that fires, with a snippet. It is not a gate and CI does not run it; a human can write a contrast scaffold, and the check still belongs on rewrites. Read it when you add or widen a banned phrase or a regex: a new hit on human prose means the check is broader than the tell. The first run showed three things worth knowing. The doubled-space check fires on the two spaces after a full stop that older technical prose uses, so a rewrite of such a source will fail it. The em-dash ban in `launch-email` fires on Jerome eleven times, which is why it stays a fixture-level ban for a strict brief and not a global check. And "be able to" and "clearly" occur in Twain, which is fine for fixtures whose ideal rewrite has no use for them, but they should never become global.

## Known-good outputs

`examples/` contains one passing rewrite per fixture (the same texts shown in the main README). They double as a self-test for the checker:

```bash
python3 evals/run_evals.py --all evals/examples
```

CI runs this self-test, together with `scripts/validate.py`, on every push to main and every pull request.

## What each fixture tests

| Fixture | Tests |
| --- | --- |
| `launch-email` | Slop removal with full fact preservation: date, feature names, and the UI label must survive. |
| `quarterly-report` | Specificity without invention: the rewrite must keep the named causes and must not contain any percentage, because none was given, or a deadline ("before the next quarter closes"), because the source only says "moving forward". |
| `release-notes` | Technical register: flags, filenames, version numbers, and exit codes stay exact while hype and diff-anchored wording go. |
| `voice-preservation` | The inverse test: a quirky human draft must come back with its quirks intact, not flattened into a house style. Contraction, first-person, and hedge rates must not move. |
| `chatbot-artefacts` | Near-conclusive cleanup: pasted chatbot scaffolding, an unfilled `[Your Name]` placeholder, and a decorative emoji must go while the steps and link survive. |
| `over-signposting` | Structural slop: ordinal signposting, stacked connectives, list-itis, and bold-label bullets go; all four facts survive. |
| `plain-human` | The false-positive regression: a plain human note with a single `delve` and one em dash must come back essentially unchanged, not over-edited. Voice markers must not move. |
| `marketing-copy` | Booster verbs, "isn't just", and template hooks go; the product name, the two features, and the price survive; no invented percentages, user counts, or awards appear. |
| `academic-hedge` | Genre exemption: the passive methods sentence and the hedges ("suggest", "may inhibit", "sample size was small") must survive while "it is important to note" and the "future research" closer go. |
| `ranking-claims` | Scope-word preservation: the slop goes, and "first site", "only office", and "most payslips of any site" survive attached to their claims. Trimming a flourish or a qualifier often takes a ranking word with it, and each one is a claim. |
| `linkedin-post` | Social-post habits: the hook, the rhetorical self-answer, the aphorism, and the engagement bait go, and the one-line broetry paragraphs collapse into prose; the facts and the opinion survive. |

## Check format

`checks.json` fields:

- `brief`: the rewrite instruction to give the skill.
- `required`: case-insensitive words or phrases that must appear in the rewrite (preserved facts). Matching is whole-word, treats spaces, hyphens, and dashes between words as equivalent, and allows a trailing inflection ("sync" matches "syncs", "profile" matches "profiling"). Leading dashes are literal, so `--dry-run` needs the flag, not "dry run".
- `required_regex`: regular expressions that must match, for a fact with more than one acceptable wording (for example "every hour" or "hourly"). Matching is case-insensitive.
- `banned`: case-insensitive words or phrases that must not appear (tells and slop). Matching works like `required` and also catches an `-ly` form, so `seamless` catches "seamlessly" and `empower` catches "empowering". List the base word, not a stem.
- `banned_regex`: regular expressions that must not match (for example invented percentages). Matching is case-insensitive.
- `max_words_ratio` / `min_words_ratio`: rewrite length bounds relative to the input, to catch padding and over-cutting.
- `voice_drift`: for keep-my-voice briefs, the largest change allowed per marker between input and rewrite. Markers are `contraction_rate`, `first_person_rate`, and `hedge_rate` (all per 100 words), `mean_word_length`, `mattr` (moving-average type-token ratio over a 25-word window, plain type-token ratio below that), and `sentence_length_sd` (the standard deviation of sentence lengths in words). The last two are the lexical-richness and style-variance signals that held up across models and domains in 2026 work (El Attar et al.; Sourati et al.); a rewrite that evens out every sentence or swaps repeated plain words for synonyms moves them. These are the four markers rewrites move even under a voice-preserving prompt (van Nuenen, "Voice Under Revision", 2026: contractions and first person fall, word length rises; Jiang and Hyland, 2025: model text carries fewer hedges). The counts are rough (a possessive counts as a contraction), but only the change matters. A rewrite of `voice-preservation` that turned "I have" and "I am" into contractions passed every other check and fails this one.

Every fixture also gets three well-formedness checks the checker applies itself: no doubled spaces inside a line, no space before punctuation (a dotfile, decimal, or ellipsis is fine), and no empty clause between punctuation marks. These catch a rewrite that only deleted the banned phrases and left the wreckage. Six structure checks run on every rewrite as well: the binary-contrast scaffolds ("not just X but Y", "isn't just", "it's not about X, it's Y", "not because X but because Y", and the split forms "This doesn't mean X. It means Y." and "This isn't about X. It's about Y."), which sam-paech's slop-score weights at a quarter of its total and which no fixture's ideal output needs.

## Adding a fixture

Keep inputs short and auditable. Seed them with tells from `references/` and at least two facts that must survive. Banned phrases should be ones a lazy rewrite would plausibly leave in or introduce; do not ban words the ideal rewrite might legitimately use. Add a known-good output to `examples/` and check it passes.
