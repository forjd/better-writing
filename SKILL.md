---
name: better-writing
description: Rewrite, draft, and review prose so it is clear, specific, human, and appropriate to context. Use this skill when improving emails, essays, documents, reports, UI copy, marketing copy, posts, or any text that may sound generic, AI-written, over-polished, verbose, salesy, evasive, or structurally formulaic. Supports voice calibration, anti-slop audits, context-aware taste decisions, and final pre-flight checks.
license: MIT
---

# Better Writing

Use this skill to make prose stronger without flattening the writer. The goal is not to make everything casual or punchy. The goal is to make the text fit its audience, purpose, and medium while removing generic AI tells, filler, fake authority, and formulaic structure.

## Core Workflow

1. Read the brief before editing.
   - Identify the audience, channel, purpose, stakes, relationship, and requested dialect.
   - Preserve required facts, citations, constraints, legal wording, quoted text, and formatting.
   - If the user gives a voice sample, treat it as the style source of truth.

2. Set the writing read.
   - State this internally unless the user wants a plan: "Reading this as: [genre] for [audience], with [tone], optimising for [outcome]."
   - Choose dials for directness, warmth, personality, density, evidence, and polish. See `references/voice-and-context.md`.

3. Audit the text.
   - For AI-writing tells, use `references/ai-writing-patterns.md`.
   - For slop phrases and formulaic structures, use `references/structures-and-phrases.md`.
   - For genre-specific fingerprints and exemptions, use `references/genre-tells.md`.
   - Work in order: scan for near-conclusive artefacts first; then count clustered tells in context; then apply genre exemptions; never edit on a single feature.
   - Look for clusters of tells, not isolated quirks. The most durable tell is uniform tone that never adapts to audience or genre. Do not destroy valid style just because it is polished.

4. Rewrite.
   - Keep the meaning and coverage unless the user asks for cuts.
   - Replace vague claims with specific facts, examples, actors, numbers, or sources.
   - Prefer active voice and simple verbs when they make the sentence clearer.
   - Vary sentence length. Avoid a steady mid-length cadence.
   - Remove chatbot framing, throat-clearing, generic conclusions, and manufactured drama.

5. Self-audit and revise.
   - Ask: "What still sounds generic, evasive, or AI-written?"
   - Fix the answer before delivering.
   - Run the pre-flight checklist in `references/preflight.md`.

## Default Output

Match the user's requested deliverable.

- For a rewrite request, return the final rewritten text first.
- For a review request, return specific findings before any rewrite.
- For a draft-from-scratch request, deliver the finished draft, not an outline unless the user asked for one.
- Include a short change note only when useful.
- Do not expose a long diagnostic audit unless the user asks for it or the risk is high.

When the user asks to "humanise", "de-AI", "remove slop", "make this sound less ChatGPT", or similar, use a stricter pass:

- Remove em dashes and en dashes when this pass is requested, using sentence breaks, commas, colons, parentheses, or regular hyphens; keep en dashes in numeric and date ranges. This is a register choice, not detector-evasion. See `references/ai-writing-patterns.md` for the full dash policy, including the lighter touch in normal rewrites.
- Remove decorative emojis, mechanical bold labels, title-case headings, and inline-header bullet lists unless the target medium expects them.
- Remove "let me know", "here is", "of course", knowledge-cutoff disclaimers, and other pasted chatbot artefacts.
- Remove vague positive endings. End on the real point.

## Editing Principles

- Specific beats impressive. Name the person, object, constraint, date, place, evidence, or trade-off.
- Direct beats announced. Do the thing instead of saying "let's explore" or "here's what matters".
- Context beats blanket rules. A support email, a board memo, a product page, and a personal essay need different levels of warmth and polish.
- Voice beats cleanliness. Preserve human asides, mixed feelings, unusual details, and defendable quirks.
- Evidence beats authority theatre. Replace "experts say" with the named source or remove the claim.
- Trust the reader. Cut hand-holding, moralising, and permission-giving unless the relationship calls for reassurance.

## Guardrails

- Do not invent facts, quotes, names, studies, links, or statistics to make prose feel concrete.
- Do not make neutral reference, legal, medical, financial, or technical text more opinionated than the genre allows.
- Do not remove nuance that protects accuracy.
- Do not over-compress if it drops required coverage.
- Do not rewrite quoted text unless the user explicitly asks.
- Preserve code identifiers, API names, product names, regulatory terms, and exact UI labels unless the task is to rename them.

## References

- `references/voice-and-context.md`: audience, genre, dials, voice calibration, and genre exemptions.
- `references/ai-writing-patterns.md`: AI-writing tells, confidence tiers, near-conclusive artefacts, and false-positive checks.
- `references/structures-and-phrases.md`: slop phrase and structure audit.
- `references/genre-tells.md`: genre-specific phrase banks for email, social, marketing, academic, and code.
- `references/preflight.md`: final delivery checks and scoring.
- `references/sources.md`: source projects and attribution notes.
