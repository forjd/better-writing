# Genre Tells

Concrete AI-writing fingerprints by genre, plus the exemptions that stop the general lists from over-editing a genre where a "tell" is actually correct. Apply the bank that matches the text. For dials, audience, and voice calibration, see `voice-and-context.md`.

## Email and Business Messages

Cut the hollow openers and framing verbs that delay the point:

- "I hope this email finds you well", "Hope all is well", "Trust you are well"
- "I wanted to reach out", "I just wanted to touch base", "Just following up", "Just checking in"
- "Please advise", "As per my last email", "Per my previous message"
- "Circle back", "touch base", "loop you in"

Fix by leading with the reason for the message, the ask, the owner, and the date. Keep enough warmth for the relationship; direct does not mean cold.

## LinkedIn and Social

- broetry: one-line paragraphs stacked for drama, each on its own line.
- engagement bait: "Agree?", "Thoughts?", "Who's with me?". See `structures-and-phrases.md`.
- manufactured-insight hooks: "Here's what nobody tells you about", "Unpopular opinion:". See Engagement Bait in `structures-and-phrases.md`.
- themed-emoji bookending and emoji bullet markers.

Fix by making one real claim and ending on it. Cut the performance.

## Marketing and SEO

Replace booster verbs and reveal framing with proof, usage, and outcomes:

- booster verbs: "supercharge", "elevate your", "unlock the power / potential / secrets of", "harness the power of", "take it to the next level", "revolutionise the way"
- urgency: "stay ahead of the curve", "future-proof your", "look no further", "now more than ever"
- SEO scaffolding: "Welcome to our comprehensive guide", "The Ultimate Guide to", "Everything You Need to Know About", "Here's a breakdown of everything you need to know", keyword-stuffed headings, padded FAQ sections
- corporate data-speak: "deliver actionable insights", "drive data-driven decisions", "leverage complex datasets"

Fix with one clear promise backed by a concrete feature, number, or example. Do not invent social proof, metrics, awards, or customer names.

## Academic and Scientific

Tells:

- excess-vocabulary stacking: "meticulously delving into the intricate", "a growing body of literature", "has garnered significant attention"
- empty imperatives: "it is imperative", "this study sheds light on", "future research should explore"
- vague evidence: "studies have shown", "research suggests" with no named trial, dataset, or author

Fix by naming the specific study, dataset, method, or result.

Exemptions, so the general lists do not damage correct scientific prose:

- Hedging is bidirectional here. A genuine hedge ("these results suggest", "under these conditions") protects accuracy and should be kept, sometimes added. Do not strip it the way you would strip marketing hedging.
- Passive voice is correct in a methods section. Do not force a human actor where the procedure is the subject.
- A real citation for every claim is the genre norm, not padding.

## Code, Pull Requests, and Documentation

Tells:

- comments that restate the obvious: "// loop over the items", "This function is responsible for"
- diff-anchored prose in docs and PRs: "we added", "now we handle", "this was changed to". Documentation should describe how the system works in the present tense. This overlaps with the Documentation note in `voice-and-context.md`; keep them consistent.
- verbose PR descriptions that narrate the diff line by line instead of stating intent and risk
- gitmoji or emoji in commit messages where the project does not use them
- over-defensive caveats and reimplementation of code that already exists

Fix by deleting comments that repeat the code, describing behaviour in the present tense, and keeping identifiers, flags, filenames, version numbers, and exit codes exact.

Exemptions:

- Bullet lists, tables, and headers are correct in reference docs and release notes.
- Markdown is correct where the destination renders it.
- "robust", "scalable", and similar words have precise technical meaning; keep them when used accurately.
