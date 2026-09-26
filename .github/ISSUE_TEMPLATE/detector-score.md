---
name: Detector score question
about: My rewrite still scores as AI. Read this first.
title: "[detector] "
labels: question
---

# Please read before filing

Beating AI detectors is explicitly a non-goal of this skill. See [What it will not do](../../README.md#what-it-will-not-do) and [why detector scores are not a check](../../evals/README.md#why-detector-scores-are-not-a-check).

- The skill improves clarity, specificity, and voice fit. It does not lower detector scores, and no edit can guarantee one.
- Optimising against a detector rewards worse prose: Pangram's own analysis found the more readable and fluent the text, the more likely it is to be detected.
- The signal is unstable: light AI edits are flagged 38% to 80% of the time while unmodified human prose is flagged 9% to 15%, and adversarial paraphrasing cuts detection by around 88%.
- The bias is real: essays by English language learners, dialect, teen, and informal writing are over-flagged across detectors.
- If you ask the skill to pass a detector, it runs the strict pass and says so in the change note, without evasion tricks such as synonym swaps, inserted typos, look-alike characters, or translation round-trips. They make the prose worse, and leading detectors are now trained on humaniser output.

Such issues are closed as working as intended unless they bring new evidence about prose quality. If your rewrite reads badly, file a bug report instead and say what reads badly.

If you still want to file, complete the details below. Most detector questions are answered by the notes above and need no further action.

## Details (optional)

- Detector name and score, before and after the rewrite:
- What reads badly in the rewrite, if anything:
- Input text or fixture name, if you can share it:
