# Evals

Regression tests for the skill. Each fixture is a text seeded with known AI tells and known facts. A passing rewrite removes the tells and keeps the facts. The checker is dependency-free Python.

This directory is repo tooling. Agents using the skill do not load it.

## Workflow

1. For each fixture in `fixtures/`, run the skill on `input.md` using the `brief` from its `checks.json` as the instruction.
2. Save each rewrite to an output directory as `<fixture-name>.md`.
3. Run the checker:

```bash
# One fixture
python3 evals/run_evals.py evals/fixtures/launch-email my-outputs/launch-email.md

# All fixtures
python3 evals/run_evals.py --all my-outputs
```

The checker exits non-zero on any failure. Run it before and after any change to `SKILL.md` or the pattern lists in `references/`.

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

## Check format

`checks.json` fields:

- `brief`: the rewrite instruction to give the skill.
- `required`: case-insensitive substrings that must appear in the rewrite (preserved facts).
- `banned`: case-insensitive substrings that must not appear (tells and slop).
- `banned_regex`: regular expressions that must not match (for example invented percentages).
- `max_words_ratio` / `min_words_ratio`: rewrite length bounds relative to the input, to catch padding and over-cutting.

## Adding a fixture

Keep inputs short and auditable. Seed them with tells from `references/` and at least two facts that must survive. Banned phrases should be ones a lazy rewrite would plausibly leave in or introduce; do not ban words the ideal rewrite might legitimately use. Add a known-good output to `examples/` and check it passes.
