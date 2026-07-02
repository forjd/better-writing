# Changelog

The pattern lists in `references/` are a living catalogue, not a fixed rulebook. AI writing tells drift as models change, so additions, changes, and retirements are dated here. When a tell fades from current model output, mark it as legacy in the reference rather than deleting it, so the skill still catches older drafts.

## 2026-07-02

### Added

- CI (`.github/workflows/ci.yml`): every push and pull request runs `scripts/validate.py` (frontmatter, fixture, and symlink checks) plus the checker self-test against `evals/examples/`.
- `agents/openai.yaml` is now linked into the `skills/better-writing/` tap, and the README documents the tap's symlink caveat for Windows checkouts and ZIP downloads.

### Changed

- The placeholder rule is now consistent across files. A template placeholder the writer forgot to fill (`[Your Name]`) stays a near-conclusive artefact; a deliberate gap marker for a missing fact (`[figure needed from the Q1 report]`) is explicitly allowed in `references/ai-writing-patterns.md`, `references/preflight.md`, and `references/voice-and-context.md`, matching the behaviour the `quarterly-report` fixture rewards.
- `references/genre-tells.md` now points manufactured-insight hooks at Engagement Bait in `references/structures-and-phrases.md`, the section that lists them, instead of Emphasis Crutches.
- The `release-notes` fixture no longer bans the em dash. Its brief asks for a plain technical register, not a strict de-AI pass, and the dash policy only strips dashes when that pass is requested.
- `evals/run_evals.py` reports a missing rewrite in `--all` mode as FAIL rather than SKIP, and treats an explicit zero length ratio as set.

## 2026-06-15

Catalogue refresh informed by 2024–2026 corpus research (Kobak, Liang, Zhao excess-vocabulary studies; the CMU/Reinhart grammar study; the current Wikipedia "Signs of AI writing" catalogue; detector false-positive research).

### Added

- A decision procedure and three confidence tiers in `references/ai-writing-patterns.md`, so "look for clusters, not isolated quirks" is now quantitative.
- A "Near-Conclusive Artefacts" section: leaked tool markup (`oaicite`, `contentReference`, and similar), raw markdown in plain-text destinations, tracking parameters, unedited chatbot scaffolding, and unfilled placeholders. These are hard evidence and need no corroboration.
- A "Nominalisation and Noun Density" pattern, a "Sycophancy" entry (2025-era), and diagnostic-only model fingerprints.
- New stock openers, mechanical transitions, and essay-scaffold closers in `references/structures-and-phrases.md`, plus structures: isn't-just escalation, countdown/tail negation, rhetorical self-answer, over-signposting, false balance, list-itis, fractal recap, invented compound jargon, aphorism formula, meta-commentary joiners, and engagement bait. Each carries a genre exemption.
- A new reference, `references/genre-tells.md`: concrete phrase banks and exemptions for email, social, marketing/SEO, academic, and code/PR/docs.
- Structure checks in `references/preflight.md`: uniform-cadence, paragraph-reshuffle, and friction-free-tone, the last worded to surface existing tone rather than invent it.
- Three eval fixtures: `chatbot-artefacts`, `over-signposting`, and `plain-human` (a false-positive regression that fails if a lone `delve` or em dash is over-edited).

### Changed

- The overused-vocabulary list is now era-stamped and tiered. Spoken-English-only and ordinary-English words that over-flag were removed or demoted to the corpus-only tier.
- The False Positives section now carries the detector equity data (Stanford 61% non-native false-positive rate; retired OpenAI classifier; the Constitution flagged as AI) and states plainly that detector-evasion is a non-goal.
- The em-dash guidance across `SKILL.md`, `references/ai-writing-patterns.md`, and `references/preflight.md` is reframed: the em dash is the least reliable single tell, removal in a strict pass is a register choice, not detector-evasion.

### Marked legacy

- The 2023 GPT-4 vocabulary set (delve, tapestry, testament, intricate, meticulous, pivotal, underscore, realm, showcase) peaked in 2023–early 2024 and is declining as models adapt. It is kept for older drafts, but its absence does not clear a text.
- The standalone model disclaimers ("As an AI language model", "As of my last update") are 2022–2024-era and largely retired; conclusive when present, but their absence proves nothing.

## 2026-06-10

### Added

- Evaluation harness in `evals/`: four fixtures (`launch-email`, `quarterly-report`, `release-notes`, `voice-preservation`), a dependency-free checker, and known-good outputs.
- Before-and-after examples, source comparison table, compatibility notes, and pattern-drift policy in the README.

### Catalogue baseline

All patterns in `references/ai-writing-patterns.md` and `references/structures-and-phrases.md` as of this date form the initial catalogue, synthesised from blader/humanizer, hardikpandya/stop-slop, Leonxlnx/taste-skill, and Wikipedia's "Signs of AI writing". See `references/sources.md` for attribution.

## 2026 (pre-changelog)

- Initial release: `SKILL.md`, references, and OpenAI-compatible agent metadata.
- Dash policy aligned across files; range en dashes exempted from strict de-AI passes.
