# AI-Writing Patterns

Use this reference to find clusters of AI-generated prose. Do not treat any single pattern as proof. Many human writers use one or two of these naturally.

## How to Use This Catalogue

One feature is never a verdict. The reliable signal is a cluster of tells plus the absence of genre adaptation. AI prose stays at one pleasant altitude no matter the audience; human prose shifts register, takes sides, and varies its rhythm. Treat uniform tone across a whole piece as the most durable tell of all.

Work in this order:

1. Scan for near-conclusive artefacts. If one is present, the text is almost certainly machine-generated or pasted from a chatbot. See below.
2. Otherwise count clustered tells in context. A passage needs several, not one. Use the confidence tiers when reading the vocabulary list.
3. Apply genre exemptions. Passive voice in a methods section, bullet lists in release notes, hedging in legal text, and markdown in a README are correct, not tells. See `voice-and-context.md` and `genre-tells.md`.
4. Never trigger an edit on a single feature. Detector-evasion is not the goal; clarity and fit are.

Confidence tiers, used throughout this file:

- Tier 1: distinctive markers. Flag when two or more appear in the same passage.
- Tier 2: common but overused. Flag only at higher density, and never replace a word on sight.
- Tier 3: ordinary English whose elevated rate shows up only across a large corpus. Do not flag or "fix" these in a single document.

## Near-Conclusive Artefacts

These need no corroboration. A single instance is hard evidence that text was machine-generated or pasted unedited from a chatbot. Remove them.

- Leaked tool and citation markup that no human types: `oaicite`, `oai_citation`, `contentReference`, `turn0search0`, `attributableIndex`, `grok_card`, `:::writing`, `【...】` citation brackets.
- Raw markdown dropped into a destination that does not render it: literal `**bold**`, `##` headings, or escaped `\*` asterisks in an email, a plain-text field, or a CMS that expected HTML.
- Tracking parameters left on pasted links, such as `?utm_source=chatgpt.com`.
- Unedited assistant scaffolding: "Let me know if you need any modifications", "Here is the revised version", "I hope this helps", "Would you like me to".
- Unfilled template placeholders the writer forgot to replace: `[Your Name]`, `[Insert X here]`, `[Company]`, `[Date]`. A deliberate editorial gap marker such as `[figure needed from the Q1 report]` is not one of these; keep it until the fact arrives.
- Standalone model disclaimers: "As an AI language model", "As a large language model", "I don't have access to real-time information". These are 2022–2024-era and largely retired by current models, so their absence proves nothing, but their presence is conclusive.

## Content Patterns

### Significance Inflation

The text overstates importance instead of explaining what happened.

Watch for:

- "serves as", "stands as", "plays a vital / crucial / pivotal / significant role"
- "testament", "pivotal", "crucial", "vital", "cornerstone", "beacon"
- "underscores its importance", "reflects broader trends", "marks a shift"
- "left an indelible mark", "deeply rooted", "a key turning point", "a focal point"
- vague claims about legacy, impact, or a changing landscape

Fix by naming the concrete event, effect, audience, or evidence.

### Notability Padding

The text lists media coverage, social presence, awards, or expert status without explaining why it matters.

Fix by using the strongest relevant fact or cutting the padding.

### Superficial Present-Participle Analysis

The text appends "-ing" phrases to simulate depth. This is one of the most durable structural tells, not a vocabulary quirk: corpus studies measure present-participial clauses in LLM prose at roughly two to five times the human rate.

Watch for:

- "highlighting", "underscoring", "reflecting", "showcasing", "contributing to", "fostering"
- trailing clauses tacked to the end of a sentence that restate the main clause instead of adding a fact

Fix by splitting the sentence and saying the actual relationship, or remove the phrase.

### Promotional Language

The prose sounds like an advert when the genre needs plain description.

Watch for:

- "boasts", "vibrant", "rich", "profound", "renowned", "groundbreaking", "stunning", "must-visit", "breathtaking"
- "in the heart of", "nestled", "commitment to excellence", "rich cultural heritage"
- abundance metaphors: "a rich tapestry of", "woven into the tapestry", "a treasure trove of", "a myriad of", "a plethora of"
- booster verbs in marketing copy: "supercharge", "unlock", "unleash", "empower", "elevate", "revolutionise", "transform". See `genre-tells.md`.

Fix with observable facts, named features, or measured claims.

### Vague Attribution

The text leans on faceless authority.

Watch for:

- "experts argue", "observers note", "industry reports suggest", "some critics say"
- "studies have shown", "research suggests", "it is widely believed" with no named source

Fix by naming the source, narrowing the claim, or removing it.

A 2025-era variant is more dangerous than vagueness: a *real* source cited for a claim it does not actually support. Current models name genuine papers, authors, and URLs but do not verify that the source backs the sentence. When a claim leans on a specific citation, check that the source says what the text says, or flag it.

### Formulaic Challenges and Future Sections

The text adds a generic "challenges", "future outlook", or "despite these challenges" section.

Fix by keeping only real constraints, dates, decisions, and next actions.

## Language Patterns

### Overused AI Vocabulary

Vocabulary tells are time-dependent, so lean on structure and cluster density over any fixed word list. The eras below show how the list drifts; the absence of an older word does not clear a text.

- 2023 (GPT-4), peaked then declined through early 2024: delve, tapestry, testament, intricate, meticulous, pivotal, underscore, realm, showcase.
- mid-2024 (GPT-4o) shift: align with, foster, highlight, enhance, garner, ensure.
- mid-2025 onward, subtler and narrower: enhance, emphasising, highlighting, showcasing, leverage, robust.

Read the list through the confidence tiers above:

- Tier 1, distinctive (flag a cluster of two or more): delve, tapestry, testament, intricate, meticulous, pivotal, underscore, realm, showcase, multifaceted, myriad, plethora, commendable, paramount, burgeoning, quintessential, cornerstone, beacon, nuanced.
- Tier 2, common but overused (flag at higher density, never replace on sight): enhance, foster, leverage, utilise, facilitate, streamline, bolster, amplify, cultivate, garner, surpass, exemplify, encompass, align with, ensure, robust, seamless, comprehensive, holistic, scalable.
- Tier 3, ordinary English (an aggregate corpus signal only, never a single-document tell): potential, significant, crucial, key, vital, notable, important, additionally, moreover, furthermore, subsequently.

Fix Tier 1 and Tier 2 clusters by using plainer words or rewriting the sentence around a concrete noun and verb. Leave Tier 3 alone in normal prose. Some Tier 2 words, such as "robust" and "scalable", carry precise technical meaning in code and documentation; keep them when accurate. See `genre-tells.md`.

### Nominalisation and Noun Density

AI prose buries actions inside abstract nouns, producing dense, noun-heavy sentences with weak verbs. Corpus studies find nominalisations at roughly 1.5 to 2 times the human rate.

Watch for:

- "the implementation of", "the utilisation of", "the optimisation of", "the facilitation of"
- "provides an improvement in" instead of "improves"
- strings of abstract nouns joined by "of": "the enhancement of the efficiency of the process"

Fix by turning the noun back into a verb: "the implementation of X" becomes "we built X" or "implementing X". Name who did what.

### Copula Avoidance

The prose dodges simple "is", "are", or "has" constructions.

Watch for:

- "serves as", "stands as", "marks", "represents", "features", "boasts"
- "refers to" used to define a subject the sentence could simply state

Fix by using the simpler verb when it is accurate.

### Negative Parallelism

The text uses a predictable contrast structure. The same pattern appears as "Binary Contrast" in `structures-and-phrases.md`; keep the two lists in sync.

Watch for:

- "not only X but Y"
- "not just X, it is Y"
- "this is not about X, it is about Y"
- the escalating variant that climbs to a grand abstraction: "X isn't just Y, it's [paradigm / engine / heartbeat]"

Fix by stating the point directly.

### Rule of Three

The prose keeps packing ideas into threes.

Fix by using the exact number the thought needs. Two is often enough. One strong example often beats a trio. A single tricolon is a normal rhetorical device, not a tell; the signal is the habit repeating across a piece.

### Synonym Cycling

The same thing gets renamed for variety: "the protagonist", "the central figure", "the hero".

Fix by choosing the clearest term and repeating it when repetition helps.

### False Ranges

The text uses "from X to Y" where the endpoints are not a real range.

Fix by naming the covered topics directly.

### Passive Voice and Subjectless Fragments

The sentence hides who acted or drops the subject.

Fix by naming the actor when it matters. Keep passive voice when the actor is unknown, irrelevant, legally sensitive, or where the genre expects it, such as a scientific methods section.

## Formatting and Style Patterns

### Dash Dependence

AI prose can lean on em dashes and en dashes for rhythm and faux sophistication. Treat this carefully: the em dash is the most-publicised tell and the least reliable. Many strong human writers use it heavily, frontier models reduced em-dash output through late 2025, and some writers now self-censor real punctuation to dodge suspicion. A single em dash, or em dashes in literary and editorial long-form, is not a tell.

In normal rewrites, treat heavy dash use as one tell among others and thin it out only when it clusters with other patterns and clearly substitutes for sentence structure. In strict "humanise" or de-AI passes, removing em and en dashes is a register choice the user has asked for, not proof of AI origin: use a period, comma, colon, parentheses, or regular hyphen instead. Either way, keep en dashes in numeric and date ranges such as "2019–2024" or "pages 10–12"; that is standard typography. Stripping dashes to beat a detector is not a quality goal.

### Mechanical Bold and Inline Headers

Watch for bullet lists where every item starts with a bold label and colon.

Fix by writing normal sentences, simpler bullets, or a table when comparison matters. A minor related tell: the bold label ending in a full stop instead of a colon, such as "**Speed.**" rather than "**Speed:**".

### Title-Case Headings

Use sentence case unless the style guide says otherwise.

### Decorative Emoji

Remove decorative emoji in professional, technical, reference, and de-AI rewrites. Keep them only when the medium and voice clearly call for them. Section-heading emoji and emoji used as bullet markers are a strong chatbot tell.

### Curly Quotes

Curly quotes alone are not an AI tell. Convert to straight quotes only when the output format, code context, or user preference requires it.

## Communication Artefacts

Remove pasted chatbot behaviour:

- "Of course", "Certainly", "Sure", "Absolutely"
- "Great question", "I'd be happy to", "Happy to help"
- "I hope this helps"
- "Let me know if you want", "Feel free to reach out"
- "Here is an overview", "Let me break this down for you", "Let me walk you through it"
- "As of my last update"
- "Based on available information" when used to pad a gap

### Sycophancy

A 2025-era artefact of assistant-tuned models: content-free praise before the substance.

Watch for:

- "You're absolutely right", "That's a brilliant question", "What a thoughtful observation"

This is a tell mainly in assistant-voiced output and in finished documents where a conversational acknowledgement makes no sense. Enthusiastic humans say these things too, so flag them when they precede the real content as filler, not when they carry genuine warmth in a message.

## Filler, Hedging, and Fake Depth

Watch for:

- "in order to", "due to the fact that", "at this point in time"
- "it is important to note", "worth noting", "when it comes to"
- "could potentially possibly be argued"
- "at its core", "the real question is", "the heart of the matter"
- "the future looks bright", "exciting times lie ahead"

Fix by cutting the phrase or writing the concrete claim.

## Model Fingerprints (diagnostic only)

For review and diagnosis tasks, not for verdicts. These date fast and a wrong attribution is worse than none, so never act on them alone.

- ChatGPT: tricolons, additive em dashes, aggressive bold, clinical vocabulary. GPT-5-era output is softer and less formal.
- Claude: long hedged multi-clause sentences, headers everywhere, first-person politeness, "you're absolutely right".
- Gemini: verbose, corporate-flat, plain conversational vocabulary, list and header heavy.

## False Positives

Do not over-edit these without a cluster of other tells:

- polished grammar, formal vocabulary, dry prose
- one transition word, one dash, one curly quote
- a single instance of a focal word such as "delve" or "intricate"
- a single tricolon or one "not X but Y" antithesis
- one warm "happy to help" in a genuine message
- a common salutation or sign-off
- clean formatting from a CMS or document editor

Why single features are unreliable, and why detector-evasion is a non-goal:

- Detectors are biased and brittle. A Stanford study found that more than half of non-native English essays were misclassified as AI across seven detectors, while near-native essays passed. Detectors have flagged founding documents such as the US Constitution as AI-written. OpenAI retired its own classifier in 2023 after it correctly flagged only 26% of AI text. Light paraphrasing defeats most detectors.
- Plain, predictable, low-variation prose is the normal style of fluent non-native, formal, and neurodivergent writers. Flagging it penalises people, not machines.
- "delve" is an RLHF artefact, not, as sometimes claimed, a marker of Nigerian English; corpus work found it does not originate there. It is common in fluent Nigerian, Indian, and other non-native business English. One or two focal words mean nothing; only a dense cluster in a short passage is a signal.
- The em dash is the least reliable single tell. See Dash Dependence.

Never strip a feature on a single signal. The job is to make the writing fit its purpose, not to make it pass a detector.

## Human Signals to Preserve

Preserve:

- specific, unusual details
- mixed feelings and unresolved tension
- dated or subculture-specific references
- first-person choices that fit the genre
- genuine asides and self-corrections
- varied sentence length
- plain repeated terms that improve clarity
- a single em dash, a lone "delve", or one tricolon used naturally
