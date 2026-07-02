# Voice and Context

Use this reference when the request is not just "fix grammar". It helps choose the right kind of good.

## Brief Read

Before rewriting, identify:

- Genre: email, essay, report, documentation, UI copy, marketing copy, social post, speech, proposal, reference text.
- Audience: peer, customer, executive, regulator, hiring manager, friend, broad public, specialist reader.
- Relationship: warm, distant, corrective, collaborative, persuasive, instructional, apologetic.
- Stakes: low-risk note, public-facing copy, legal or compliance-sensitive text, high-trust technical guidance.
- Outcome: inform, persuade, reassure, ask, decline, explain, sell, document, announce, apologise.
- Constraints: length, dialect, house style, forbidden claims, citations, exact wording, formatting.

Then form a one-line read:

`Reading this as: [genre] for [audience], with a [tone] voice, optimising for [outcome].`

Do not show this line unless planning helps the user.

## Dials

Set these mentally before rewriting. Adjust them from the brief rather than using one house style.

| Dial | Low | High |
| --- | --- | --- |
| Directness | gentle, indirect, relationship-preserving | concise, plain, no ceremony |
| Warmth | cool, formal, restrained | personal, generous, conversational |
| Personality | invisible editor | distinctive point of view |
| Density | spacious, accessible | compressed, expert-facing |
| Evidence | common-sense, experiential | sourced, quantified, caveated |
| Polish | rough human texture | publication-ready finish |

## Genre Defaults

This section sets the dials and the exemptions for each genre. For the concrete phrase banks per genre, see `genre-tells.md`.

A tell in one genre is correct in another. Before applying the general lists, check these exemptions:

- Passive voice is correct in a scientific methods section.
- Hedging is correct, and sometimes should be added, in academic, legal, and medical prose.
- Bullet lists, tables, and headers are correct in technical docs, release notes, reference material, and checklists.
- Markdown is correct where the destination renders it.
- Words like "robust" and "scalable" have precise technical meaning; keep them when accurate.

### Emails

- Lead with the action or decision.
- Keep goodwill, but cut servility.
- Use concrete asks, owners, dates, and next steps.
- Preserve relationship context. Direct does not mean blunt.

### Documentation and Technical Writing

- Prefer present-tense descriptions of how the system works.
- Remove diff-anchored wording such as "this was added to".
- Keep identifiers exact.
- Use active voice where it clarifies ownership, but do not force a human actor where the system is the true actor.

### Product and Marketing Copy

- Replace hype with proof, usage, contrast, and concrete outcomes.
- Avoid "elevate", "seamless", "unlock", "next-gen", and vague "transform your workflow" language.
- Do not invent social proof, customer names, usage metrics, awards, or benchmarks.
- Use one clear promise rather than a pile of benefits.
- See `genre-tells.md` for the fuller bank of booster verbs and SEO scaffolding.

### Essays, Posts, and Opinion

- Let the writer have a position, uncertainty, or tension.
- Keep strange details and lived examples.
- Vary rhythm. A few short sentences are useful; a whole page of staccato lines feels manufactured.
- Avoid tidy moral conclusions unless the piece has earned them.

### Reference, Legal, Medical, Financial, and Policy Text

- Keep the voice plain and neutral.
- Preserve caveats that protect accuracy.
- Do not add personality for its own sake.
- Verify unstable facts if the answer depends on current law, prices, policy, availability, or research.

## Voice Calibration

If the user provides a writing sample, read it before editing and note:

- sentence length and paragraph rhythm
- vocabulary level and favourite plain words
- punctuation habits
- transitions and paragraph openings
- use of humour, asides, uncertainty, and first person
- preferred level of compression

Match patterns from the sample instead of replacing them with generic "good writing". Preserve recurring quirks when they feel intentional and do not hurt clarity.

## Specificity Ladder

When a sentence feels vague, climb this ladder until it becomes useful:

1. Name the actor.
2. Name the object or system.
3. Name the action.
4. Add a number, date, place, example, source, or consequence.
5. Cut the sentence if it still only says "this is important".

## Fact Safety

Concrete prose can tempt an agent to fabricate. Do not do that.

- If a fact is missing, ask for it, mark the gap with a clear placeholder such as `[figure needed from the Q1 report]`, or write around it honestly. Never fill the gap with an invented specific.
- Mark uncertain claims as uncertain without using filler.
- Do not turn "some people say" into named experts unless the source is available.
- Do not add invented anecdotes to make a piece sound human.
