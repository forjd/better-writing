# Evals

Regression tests for the skill. Each fixture is a text seeded with known AI tells and known facts. A passing rewrite removes the tells and keeps the facts. Both scripts are dependency-free Python.

This directory is repo tooling. Agents using the skill do not load it.

## Workflow

Run every fixture through a real model with the skill loaded, then check the rewrites:

```bash
python3 evals/run_skill.py                       # all fixtures, claude-opus-5
python3 evals/run_skill.py --model claude-sonnet-5 launch-email plain-human
```

The runner builds a system prompt from `SKILL.md` plus every file in `references/`, sends each fixture's `input.md` with its `brief` through `claude -p` with no tools, saves the rewrite to `evals/outputs/<fixture-name>.md` (gitignored), and runs the checker on it. It needs the Claude Code CLI on PATH with working credentials. Run it before and after any change to `SKILL.md` or the pattern lists and compare the reports, and read the outputs, since a pass count says nothing about whether the prose reads well. The report's first line names the model, because length and formatting defaults differ between models.

After the checker, the runner makes a second model call that lists every claim in the rewrite the input does not state or imply: a next step, a line about what has happened since, an opinion or joke the source lacks. One listed claim fails the fixture, and the list is saved next to the rewrite as `<fixture-name>.claims.json`. This exists because the substring checker cannot see invention: a rewrite that added "nobody has asked to bring the stand-up back" to the LinkedIn fixture passed every substring check. Read a flagged claim before acting on it. With `claude-opus-5` as judge, the ten known-good examples pass and the three inventions seen in real runs are all listed. A smaller judge over-flags: `claude-sonnet-5` listed changes in attribution strength that the prompt tells it to ignore, so keep the judge on the default model. Pass `--no-judge` to skip the call and `--judge-model` to override it.

To check rewrites you produced some other way, save them as `<fixture-name>.md` and run the checker directly:

```bash
python3 evals/run_evals.py evals/fixtures/launch-email my-outputs/launch-email.md
python3 evals/run_evals.py --all my-outputs
```

The checker exits non-zero on any failure.

## Known-good outputs

`examples/` contains one passing rewrite per fixture (the same texts shown in the main README). They double as a self-test for the checker:

```bash
python3 evals/run_evals.py --all evals/examples
```

CI runs this self-test, together with `scripts/validate.py`, on every push and pull request.

## What each fixture tests

| Fixture | Tests |
| --- | --- |
| `launch-email` | Slop removal with full fact preservation: date, feature names, and the UI label must survive. |
| `quarterly-report` | Specificity without invention: the rewrite must keep the named causes and must not contain any percentage, because none was given. |
| `release-notes` | Technical register: flags, filenames, version numbers, and exit codes stay exact while hype and diff-anchored wording go. |
| `voice-preservation` | The inverse test: a quirky human draft must come back with its quirks intact, not flattened into a house style. |
| `chatbot-artefacts` | Near-conclusive cleanup: pasted chatbot scaffolding, an unfilled `[Your Name]` placeholder, and a decorative emoji must go while the steps and link survive. |
| `over-signposting` | Structural slop: ordinal signposting, stacked connectives, list-itis, and bold-label bullets go; all four facts survive. |
| `plain-human` | The false-positive regression: a plain human note with a single `delve` and one em dash must come back essentially unchanged, not over-edited. |
| `marketing-copy` | Booster verbs, "isn't just", and template hooks go; the product name, the two features, and the price survive; no invented percentages, user counts, or awards appear. |
| `academic-hedge` | Genre exemption: the passive methods sentence and the hedges ("suggest", "may inhibit", "sample size was small") must survive while "it is important to note" and the "future research" closer go. |
| `linkedin-post` | Social-post habits: the hook, the rhetorical self-answer, the aphorism, and the engagement bait go, and the one-line broetry paragraphs collapse into prose; the facts and the opinion survive. |

## Check format

`checks.json` fields:

- `brief`: the rewrite instruction to give the skill.
- `required`: case-insensitive substrings that must appear in the rewrite (preserved facts).
- `banned`: case-insensitive substrings that must not appear (tells and slop).
- `banned_regex`: regular expressions that must not match (for example invented percentages).
- `max_words_ratio` / `min_words_ratio`: rewrite length bounds relative to the input, to catch padding and over-cutting.

Every fixture also gets three well-formedness checks the checker applies itself: no doubled spaces inside a line, no space before punctuation, and no empty clause between punctuation marks. These catch a rewrite that only deleted the banned phrases and left the wreckage.

## Adding a fixture

Keep inputs short and auditable. Seed them with tells from `references/` and at least two facts that must survive. Banned phrases should be ones a lazy rewrite would plausibly leave in or introduce; do not ban words the ideal rewrite might legitimately use. Add a known-good output to `examples/` and check it passes.
