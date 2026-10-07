# Contributing

Thanks for helping. This file covers what to change where, how to check a change, and how to open the pull request.

## Keep the skill lean

Put core workflow guidance in [SKILL.md](./skills/better-writing/SKILL.md), and move detailed pattern lists or examples into [references/](./skills/better-writing/references/). Both live in `skills/better-writing/`. Keep every file the skill needs in that folder as a real file, because skills.sh and manual installs copy that folder only. Do not add a `SKILL.md` at the repo root: skills.sh would then install the whole repo, and Claude Code would load the skill twice. If you change `LICENSE`, copy it to `skills/better-writing/LICENSE` as well; `scripts/validate.py` checks that the two match. Agents load `SKILL.md` on every trigger and the references only when needed, so every line in `SKILL.md` costs something.

Avoid bulky documentation the agent does not need. Keep examples factual, concise, and easy to audit.

## Adding a newly observed tell

Pull requests adding tells are welcome. Bring at least one real example of the tell in model output and a false-positive note: where the same word or structure is fine in human writing. Date the addition in [CHANGELOG.md](./CHANGELOG.md). Changes and retirements get dated too; a pattern that fades from current model output is marked as legacy rather than deleted.

## Checking a change

Run the repo checks. CI runs the same four on every pull request:

```bash
python3 scripts/validate.py                  # frontmatter, fixtures, splits, symlinks, agent configs
python3 scripts/lint_prose.py                # the repo docs pass the skill's own audit
python3 evals/run_evals.py --all evals/examples  # checker self-test against the hand-written examples
python3 -m unittest discover -s tests            # unit tests for the scripts and the eval statistics
```

If you touched `SKILL.md` or anything in `references/`, run the evals with a real model before and after the change:

```bash
python3 evals/run_skill.py --split dev --arm both --repeats 5
```

Say in the pull request what changed between the two reports, and read the rewrites in `evals/outputs/` as well as the pass counts. Tune on the dev split only; the held-out fixtures are for confirmation. The runner needs the Claude Code CLI on PATH with working credentials. [evals/README.md](./evals/README.md) explains the arms, the repeats, the intervals, and how to add a fixture.

## Opening the pull request

- Use a [conventional commit](https://www.conventionalcommits.org/) title, since release-please sets the version from it: `feat:` for new patterns, checks, or fixtures, `fix:` for corrections, and `feat!:` or a `BREAKING CHANGE:` footer for anything listed under [Releases](./README.md#releases).
- Do not edit version numbers by hand. release-please bumps them.
- Write new prose in British English with sentence-case headings. The repo's own docs follow the catalogue.

## Reporting problems

Use the [issue templates](https://github.com/forjd/better-writing/issues/new/choose). If the skill over-edited clean prose, include the input, the brief, and the output. Questions about AI-detector scores are answered in [why detector scores are not a check](./evals/README.md#why-detector-scores-are-not-a-check). For security issues, follow [SECURITY.md](./SECURITY.md) instead of opening a public issue.
