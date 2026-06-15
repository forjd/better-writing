# Sources

This skill is a new synthesis informed by these public sources:

- `blader/humanizer`: https://github.com/blader/humanizer
  AI-writing pattern taxonomy, voice calibration, false-positive caution, and draft-audit-final loop.
- `hardikpandya/stop-slop`: https://github.com/hardikpandya/stop-slop
  Sharper anti-slop checks for throat-clearing, binary contrast, false agency, filler phrases, and rhythm.
- `Leonxlnx/taste-skill`: https://github.com/Leonxlnx/taste-skill
  Context-first brief reading, explicit quality dials, anti-default discipline, and pre-flight matrices.
- `Wikipedia:Signs of AI writing`: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
  Observed patterns in AI-generated prose, especially significance inflation, vague attribution, promotional tone, formulaic structure, and overused vocabulary.

## Corpus and detection research (2023–2025)

These informed the 2026-06-15 refresh: confidence tiers, era stamping, the nominalisation and present-participle patterns, and the false-positive guardrails.

- Kobak et al., "Delving into LLM-assisted writing in biomedical publications through excess vocabulary": https://arxiv.org/abs/2406.07016
  Measured excess word usage across over 15M PubMed abstracts (2010–2024); the source of the "delve" and excess-vocabulary evidence.
- Juzek and Ward, "Why Does ChatGPT 'Delve' So Much? Exploring the Sources of Lexical Overrepresentation in LLMs", COLING 2025: https://arxiv.org/abs/2412.11385
  Tested and rejected the Nigerian-English hypothesis for "delve"; the basis for treating it as an RLHF artefact rather than a dialect marker.
- Liang et al., "Mapping the Increasing Use of LLMs in Scientific Papers": https://arxiv.org/abs/2404.01268
  Corpus estimate of LLM-modified text across arXiv, bioRxiv, and Nature journals; the realm/intricate/showcasing/pivotal vocabulary cluster.
- Reinhart et al., "Do LLMs write like humans? Variation in grammatical and rhetorical styles", PNAS 2025: https://www.pnas.org/doi/10.1073/pnas.2422455122
  Quantified present-participial clauses at 2–5x and nominalisations at 1.5–2x the human rate; the basis for the nominalisation and noun-density pattern.
- Liang et al., "GPT detectors are biased against non-native English writers", Patterns 2023: https://arxiv.org/abs/2304.02819
  Documented misclassification of non-native English writing; the basis for the false-positive guardrails and the anti-detector-evasion stance.

Use these sources as diagnostic inspiration. Do not copy upstream examples or prose into user deliverables. When maintaining this skill, keep `SKILL.md` concise and move detailed pattern lists into references.
