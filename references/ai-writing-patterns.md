# AI-writing patterns

Use this reference to find clusters of AI-generated prose. Do not treat any single pattern as proof. Many human writers use one or two of these naturally.

## How to use this catalogue

One feature is never a verdict. The reliable signal is a cluster of tells plus the absence of genre adaptation. AI prose stays at one pleasant altitude no matter the audience; human prose shifts register, takes sides, and varies its rhythm. Treat uniform tone across a whole piece as the most durable tell of all.

Work in this order:

1. Scan for near-conclusive artefacts. If one is present, the text is almost certainly machine-generated or pasted from a chatbot. See below.
2. Otherwise count clustered tells in context. A passage needs several, not one. Use the confidence tiers when reading the vocabulary list.
3. Apply genre exemptions. Passive voice in a methods section, bullet lists in release notes, hedging in legal text, and markdown in a README are correct, not tells. See Genre defaults in `voice-and-context.md` and the per-genre Exemptions in `genre-tells.md`.
4. Never trigger an edit on a single feature. Detector-evasion is not the goal; clarity and fit are.

Confidence tiers, used throughout this file:

- Tier 1: distinctive markers. Flag when two or more appear in the same passage.
- Tier 2: common but overused. Flag only at higher density, and never replace a word on sight.
- Tier 3: ordinary English whose elevated rate shows up only across a large corpus. A single instance is never a tell. Stacked connectives are actionable — see Over-signposting in `structures-and-phrases.md`. Other Tier 3 words are actionable only inside Significance inflation or Notability padding (under Content patterns), otherwise leave them alone.

## Near-conclusive artefacts

These need no corroboration. A single instance is hard evidence that text was machine-generated or pasted unedited from a chatbot. Remove them.

- Leaked tool and citation markup that no human types: `oaicite`, `oai_citation`, `contentReference`, `turn0search0`, `citeturn1view0`, `attributableIndex`, ChatGPT's `:::writing{variant="…" id="…"}` block and its `Example+1` source-chip suffix, Grok's `grok_card`, `grok_render_citation_card_json`, and `<grok-card data-type="citation_card">`, Gemini's `[cite: 1]` and `[span_1](start_span)`, Perplexity's `[web:1]`, `attached_file`, and `ppl-ai-file-upload`, lenticular-bracket citations with a dagger such as `【85†L261-269】` (DeepSeek and Meta AI both use the form), ` ```wikitext ` fences, and links that point at a search-engine results page instead of a source.
- Invisible private-use characters (U+E000 to U+F8FF). ChatGPT wraps its `cite…` tokens in U+E200, U+E201, and U+E202, and when the visible markup is deleted the invisible characters often stay behind. They do not render, so search for them with a regex or a hex view.
- Reasoning or tool syntax written out as text: literal `<thinking>` tags, or a tool call typed as prose. Anthropic documents this for Claude Opus 5 with thinking disabled. No case in pasted text had been reported as of September 2026, but one sighting is conclusive.
- Citations that do not resolve: a DOI or ISBN that is invalid, or a DOI that resolves to an unrelated article. A 2026 audit of flagged Wikipedia articles found only 7% cited a fabricated source but over two-thirds failed verification, so check the resolving ones too.
- Humaniser residue. Commercial "humanisers" swap words for dictionary synonyms and damage the text: "counterfeit consciousness" for "artificial intelligence", tortured phrases in place of standard terms, non-standard Unicode look-alike characters, and a sudden drop to elementary register with random typos. A benchmark of 19 such tools found every one degraded the original. Treat the residue as conclusive and restore the plain term.
- Raw markdown dropped into a destination that does not render it: literal `**bold**`, `##` headings, escaped `\*` asterisks, or a markdown pipe table (`| a | b |` rows over a `|---|` separator) in an email, a plain-text field, a wiki, or a CMS that expected HTML.
- Tracking parameters left on pasted links: `?utm_source=chatgpt.com`, `utm_source=openai`, `utm_source=copilot.com`, `referrer=grok.com`.
- Unedited assistant scaffolding: "Let me know if you need any modifications", "Here is the revised version", "I hope this helps", "Would you like me to", and pasted chat labels such as "Claude responded:".
- Unfilled template placeholders the writer forgot to replace: `[Your Name]`, `[Insert X here]`, `[Company]`, `[Date]`. A deliberate editorial gap marker such as `[churn figure needed]` is not one of these; keep it until the fact arrives.
- Standalone model disclaimers: "As an AI language model", "As a large language model", "I don't have access to real-time information". These are 2022–2024-era and largely retired by current models, so their absence proves nothing, but their presence is conclusive.

## Content patterns

### Significance inflation

The text overstates importance instead of explaining what happened.

Watch for:

- "serves as", "stands as", "plays a vital / crucial / pivotal / significant role"
- "testament", "pivotal", "crucial", "vital", "cornerstone", "beacon"
- "underscores its importance", "reflects broader trends", "marks a shift"
- "left an indelible mark", "deeply rooted", "a key turning point", "a focal point"
- vague claims about legacy, impact, or a changing landscape

Fix by naming the concrete event, effect, audience, or evidence, if the source gives one. If it does not, cut the clause, or, when the brief asks to keep everything and the clause carries a real hope or judgement, keep it as one in plain words, in about as many words as the source's clause: "paving the way for a seamless rollout across the organisation" becomes "which should help the rollout across the organisation". Keep only the hope. Do not wrap it in a judgement of your own ("careful planning mattered here"), turn praise into a thanks or a sign-off ("thanks to the team in Leeds"), or give it a sentence of its own when the source gave it a clause. Never convert the inflation into a fact: "paving the way for a company-wide rollout" is a hope, not a report that the rollout has started, and "underscores the importance of planning" does not say planning caused anything.

### Notability padding

The text lists media coverage, social presence, awards, or expert status without explaining why it matters.

Fix by using the strongest relevant fact or cutting the padding.

### Superficial present-participle analysis

The text appends "-ing" phrases to simulate depth. This is one of the most durable structural tells, not a vocabulary quirk: corpus studies measure present-participial clauses in LLM prose at roughly two to five times the human rate.

Watch for:

- "highlighting", "underscoring", "reflecting", "showcasing", "contributing to", "fostering"
- trailing clauses tacked to the end of a sentence that restate the main clause instead of adding a fact

Fix by splitting the sentence and saying the actual relationship, or remove the phrase. When the source states no relationship, remove the phrase or keep it at the strength the source gave it; a trailing "-ing" clause turned into a sentence that asserts a cause or a result is an invented claim.

### Promotional language

The prose sounds like an advert when the genre needs plain description.

Watch for:

- "boasts", "vibrant", "rich", "profound", "renowned", "groundbreaking", "stunning", "must-visit", "breathtaking"
- "in the heart of", "nestled", "commitment to excellence", "rich cultural heritage"
- abundance metaphors: "a rich tapestry of", "woven into the tapestry", "a treasure trove of", "a myriad of", "a plethora of"
- booster verbs in marketing copy such as "supercharge" and "unlock". See the canonical bank under Marketing and SEO in `genre-tells.md`.

Fix with observable facts, named features, or measured claims.

### Vague attribution

The text leans on faceless authority.

Watch for:

- "experts argue", "observers note", "industry reports suggest", "some critics say"
- "studies have shown", "research suggests", "it is widely believed" with no named source
- a book cited with no page number for a specific claim — weak on its own, so ask for the page or narrow the claim

Fix by naming the source, narrowing the claim, or removing it.

When the source gives no name, narrowing means dropping the faceless-authority noun and keeping the claim at its strength. "Some internal observers suggest the pricing change may have contributed" becomes "It has been suggested internally that the pricing change may have contributed". The noun ("observers", "experts", "critics", "industry watchers") is the tell; the hedges are not. Keep each hedge as a word, not only its meaning: "suggest" and "may" both stay. Do not replace the noun with an invented one ("the finance team", "analysts"), and where the brief needs the source named, add a gap marker such as `[who raised this?]`.

A 2025-era variant is more dangerous than vagueness: a *real* source cited for a claim it does not actually support. Current models name genuine papers, authors, and URLs but do not verify that the source backs the sentence. When a claim leans on a specific citation, check that the source says what the text says, or flag it.

### Speculation from absence

The text turns a gap in the sources into a claim about the subject: "Information about her early life is not publicly available, suggesting she maintains a low profile." The second clause is invented.

Fix by stating what is documented and stopping: "Her early life is not documented in the available sources."

### Vague connection

The text asserts a relationship without saying what it is: "associated with", "linked to", "in connection with", "has been involved in", "the system has been associated with residential water management applications".

Fix by naming the relationship (built, sold, funded, tested, was sued over) or cutting the sentence.

The false range is a close relative: "from X to Y" where the endpoints are not the ends of any scale, as in "from ancient pottery to modern fintech". Wikipedia stopped listing it as a separate sign in September 2026. Treat it as a vague connection and fix it the same way, by naming the topics covered.

### Process narration

The text narrates the research instead of reporting it: "after reviewing available sources", "upon examination of the record", "a closer look reveals". A 2026 Wikipedia cleanup candidate. Fix by giving the finding and, where the genre wants it, the citation.

### Formulaic challenges and future sections

The text adds a generic "challenges", "future outlook", or "despite these challenges" section.

Fix by keeping only real constraints, dates, decisions, and next actions.

## Language patterns

### Overused AI vocabulary

Vocabulary tells are time-dependent, so lean on structure and cluster density over any fixed word list. The eras below show how the list drifts; the absence of an older word does not clear a text.

- 2023 (GPT-4), peaked then declined through early 2024: delve, tapestry, testament, intricate, meticulous, pivotal, underscore, realm, showcase.
- mid-2024 (GPT-4o) shift: align with, foster, highlight, enhance, garner, ensure.
- mid-2025 onward, subtler and narrower: emphasising, enhance, highlighting, showcasing. Grok keeps "underscore" and adds causal, empirical, correlate.
- Newer additions seen across skills and corpora in 2026: quietly (as in "quietly powerful"), gate / gated / gating used figuratively, interplay, enduring, valuable, "key" as an adjective.

Read the list through the confidence tiers above:

- Tier 1, distinctive (flag a cluster of two or more): delve, tapestry, testament, intricate, meticulous, pivotal, underscore, realm, showcase, multifaceted, myriad, plethora, commendable, paramount, burgeoning, quintessential, cornerstone, beacon, nuanced.
- Tier 2, common but overused (flag at higher density, never replace on sight): enhance, foster, leverage, utilise, facilitate, streamline, bolster, amplify, cultivate, garner, surpass, exemplify, encompass, align with, ensure, robust, seamless, comprehensive, holistic, scalable, and the abstract nouns framework, ecosystem, and dynamic (as a noun, "the team dynamic") when they name no specific thing. See Abstract metaphor nouns in `structures-and-phrases.md`.
- Tier 3, ordinary English (an aggregate corpus signal only, never a single-document tell): potential, significant, crucial, key, vital, notable, important, additionally, moreover, furthermore, subsequently. Single instances are never a tell. Flag stacked "additionally, moreover, furthermore, subsequently" only as Over-signposting in `structures-and-phrases.md`, and flag the rest only inside Significance inflation or Notability padding above.

Fix Tier 1 and Tier 2 clusters by using plainer words or rewriting the sentence around a concrete noun and verb. Leave Tier 3 alone except for stacked connectives and Significance inflation or Notability padding as above. Keep any Tier 2 word that carries precise technical meaning in code and documentation, such as "robust" and "scalable", when accurate. See Exemptions under Code, pull requests, and documentation in `genre-tells.md`.

### Nominalisation and noun density

AI prose buries actions inside abstract nouns, producing dense, noun-heavy sentences with weak verbs. Corpus studies find nominalisations at roughly 1.5 to 2 times the human rate.

Watch for:

- "the implementation of", "the utilisation of", "the optimisation of", "the facilitation of"
- "provides an improvement in" instead of "improves"
- strings of abstract nouns joined by "of": "the enhancement of the efficiency of the process"

Fix by turning the noun back into a verb: "the implementation of X" becomes "we built X" or "implementing X". Name who did what.

### Copula avoidance

The prose dodges simple "is", "are", or "has" constructions.

Watch for:

- "serves as", "stands as", "marks", "represents", "features", "boasts"
- "refers to" used to define a subject the sentence could simply state

Fix by using the simpler verb when it is accurate.

### Negative parallelism

The text uses a predictable contrast structure: "not only X but Y", "this is not about X, it is about Y". Treat repeated instances as Tier 1: one 2026 report hypothesised the construction at about three times the human rate, rising in corporate filings and public statements year on year, and surviving prompts that tell the model to stop; treat this as a diagnostic hypothesis reported second-hand, not a verified rate. The full list, the escalating variant, and the fix are under Binary contrast in `structures-and-phrases.md`.

### Rule of three

The prose keeps packing ideas into threes. LLM argumentative prose runs tricolons at close to twice the rate of expert human writers.

Fix by using the exact number the thought needs. When the source's three items overlap in meaning, merge them; when each carries a distinct fact, keep all three and vary the sentence shape instead. A single tricolon is a normal rhetorical device, not a tell; the signal is the habit repeating across a piece.

### Synonym cycling and close-repetition avoidance

The same thing gets renamed for variety: "the protagonist", "the central figure", "the hero". The underlying habit is avoiding a word close to its last use. Lexical dispersion is the strongest single predictor in a 2025 study of six diversity measures, and the habit is stronger in newer ChatGPT versions than older ones, so it is not fading.

Fix by choosing the clearest term and repeating it when repetition helps. A human writer says "the parser" four times in a paragraph.

The sources disagree on whether this is current. In September 2026 Wikipedia moved elegant variation to its historical indicators, on the premise that it came from repetition penalties in older models. This catalogue keeps it, because the 2025 study measured the habit getting stronger in newer ChatGPT versions. Either way it is Tier 2: a habit across a piece, never one renamed noun.

### Sentence length

2025-era instruction-tuned models write sentences 15 to 30% longer than human authors of comparable text, and pack them with nominal modifiers, participial phrases, and coordinated nouns. 2023-era models ran short and choppy. Neither is a single-sentence tell; the signal is a whole piece that sits at one length with no short sentence anywhere. See Uniform cadence under Structure check in `preflight.md`.

### Mannered prose

The sentence substitutes metaphor and flourish for direct statement: "the codebase groans under its own weight", "a symphony of microservices", "we set sail for a new architecture". The fix is to say what you mean. When a literal phrase is available, use it. This is similar to Anthropic's guidance for its own models, and it works on drafts too.

### Passive voice and subjectless fragments

The sentence hides who acted or drops the subject.

Scan for "is", "are", "was", "were", or "been" followed by a past participle, then ask who did it: "queries are validated" becomes "the compiler validates queries"; "the file is parsed by the loader" becomes "the loader parses the file".

Fix by naming the actor when it matters. Keep passive voice when the actor is unknown, irrelevant, legally sensitive, or where the genre expects it, such as a scientific methods section.

## Formatting and style patterns

### Dash dependence

AI prose can lean on em dashes and en dashes for rhythm and faux sophistication. Treat this carefully: the em dash is the most-publicised tell and the least reliable. Many strong human writers use it heavily, and some writers now self-censor real punctuation to dodge suspicion. A single em dash, or em dashes in literary and editorial long-form, is not a tell.

The rate depends on which model wrote the text, not on "AI"; the per-model figures are under Model fingerprints below, for diagnosis only. The habit is also fading and easy to switch off. In September 2026 Wikipedia proposed moving em-dash overuse to its historical indicators, and a one-line instruction to avoid dashes takes some current models to almost none. A text with no dashes proves nothing, and one with many proves little. A per-model rate is never, by itself, a reason to edit the writer's dashes: a dash the writer put there stays unless it clusters with other tells as described next, or the brief asks for the strict pass.

In normal rewrites, treat heavy dash use as one tell among others and thin it out only when it clusters with other patterns and clearly substitutes for sentence structure. In strict "humanise" or de-AI passes, removing em and en dashes is a register choice the user has asked for, not proof of AI origin. End the sentence or use a comma. Do not swap the dash for a colon or parentheses; see Colon as connector below. Either way, keep en dashes in numeric and date ranges such as "2019–2024" or "pages 10–12"; that is standard typography. Stripping dashes to beat a detector is not a quality goal.

### Colon as connector

A colon is correct before a list, an example, or a definition. It becomes a tell when it works as a mid-sentence hinge that adds nothing: "If you're coming from traditional automation: instead of registering event handlers, you describe conditions." The colon stands in for a connection the sentence never makes.

Fix by writing the sentence without the comparison framing, or by using a full stop. Flag the habit across a piece, not the single instance, the same caution as Dash dependence above.

### Mechanical bold and inline headers

Watch for bullet lists where every item starts with a bold label and the text after it only restates the label: "**Performance:** Performance improved across the board."

The tell is the redundancy, not the punctuation. A bold lead-in that names the item and is followed by genuinely new detail is a normal documentation convention, whether it ends in a colon or a full stop: "**Schema in TypeScript.** Tables live in one file." Keep those.

Fix the redundant kind by writing normal sentences, simpler bullets, or a table when comparison matters. The related tell is the whole list running on the same template when only two of its items need a label.

### Title-case headings

Use sentence case unless the style guide says otherwise. Exempt outlet headings where the publication's house style requires title case.

### Heading restated by its first sentence

A heading followed by a sentence that only repeats it: "## Installation" then "This section covers how to install the tool." Delete the sentence and start with the first instruction.

### Summary-shaped and paired headings

Headings that do the section's work for it ("Why the reception was mixed" where "Reception" is the heading) and reflexive "X and Y" headings ("Awards and recognition", "Challenges and opportunities"). Use the plain noun and let the section say what it says.

### Document skeleton tells

Horizontal rules between every section, skipped heading levels, a heading that contains only sub-headings, and a small table for two or three facts that are not tabular. Fix by writing the structure the content needs, not the one the model's template produces.

### Over-compression

The opposite of padding: articles and verbs dropped, arrows standing in for sentences, private abbreviations, so the reader has to decode. "Config → validated → cached; retry on fail" in a document written for someone else. Arrow chains used as a mock flow chart are the usual form in social posts. Fix by writing the sentence with its verb and articles. Exempt commit subjects, changelogs, chat between people who share the context, and notes the writer keeps for themselves.

### Hyphenated pairs after the noun

AI prose hyphenates compound modifiers everywhere. Keep the hyphen before a noun when grammar needs it ("a high-quality report") and drop it after the noun ("the report is high quality"). One stray hyphen is nothing; a piece where every pair is hyphenated in both positions is a habit.

### Decorative emoji

Remove decorative emoji in professional, technical, reference, and de-AI rewrites. Keep them only when the medium and voice clearly call for them. Section-heading emoji and emoji used as bullet markers are a strong chatbot tell.

### Curly quotes

Curly quotes alone are not an AI tell. Word processors and phones insert them, and chat models split: ChatGPT (since mid-2025) and DeepSeek emit curly quotes, Claude and Gemini straight ones. Convert to straight quotes only when the output format, code context, or user preference requires it.

## Communication artefacts

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

## Filler, performed hedging, and fake depth

Watch for:

- "due to the fact that", "at this point in time"
- "it is important to note", "worth noting", "when it comes to"
- "could potentially possibly be argued", "may potentially in some cases"
- impersonal hedges that assign a view to no one: "one might argue", "it could be said", "some would say", "it can be argued that". Cut the frame and state the claim at the strength the source gives it; if the source holds the view, it is the writer's, so write it as theirs.
- "at its core", "the real question is", "the heart of the matter"
- "the future looks bright", "exciting times lie ahead"

Fix by cutting the phrase or writing the concrete claim.

Hedging is two different things, and only one is a tell. Performed hesitancy ("it is important to note", stacked modals that hedge nothing in particular) runs at about twice the human rate in LLM argument. Stance hedges and boosters ("I think", "probably", "perhaps", "very", "tends to") are the opposite: corpus work on ChatGPT essays finds a significantly lower rate of hedges, boosters, and attitude markers than in human writing, which is what makes the prose impersonal. Strip the first kind. Keep the second, and never strip it on a keep-my-voice brief.

Wordy constructions such as "in order to" and "as a result of" belong with the second kind. Humans write them; ChatGPT and Grammarly remove them. Cut them for concision when the brief asks for tight prose. Cutting them is not a de-AI fix, and on a keep-my-voice brief they stay.

## Model fingerprints (diagnostic only)

For review and diagnosis tasks, not for verdicts. These date fast and a wrong attribution is worse than none, so never act on them alone. Two cautions from the corpus work: instruction tuning, not the vendor, drives most of the shared tells, and successive models from one vendor often do not cluster together, so a fingerprint carries a model version and a date or it is worthless.

Two more cautions for this section. Several entries rest on vendor system prompts, some official and some leaked (the leaked ones come from the asgeirtj/system_prompts_leaks collection and are unofficial). A ban in a system prompt shows the vendor saw the habit; it does not show how often the habit survives. And the phrase multiples from Graphite's September 2026 study come from web articles, so they may not carry over to chat replies or email.

- ChatGPT, GPT-4 to 4o era (2023 to 2024): tricolons, additive em dashes, bold inside enumerations, "such as", "certainly", "below is", "overall", academic register that shuns slang.
- GPT-5.x (late 2025 onward): em dashes below the human rate, softer register, curly quotes, a "Good question" or "Great start" opener reintroduced by OpenAI. The leaked GPT-5.5 Thinking prompt (May 2026) bans "If you want", "If you mean", "Short answer:", "Short version:", and ending a reply on "I can …", which suggests those were habits. Creature metaphors ("goblin", "gremlin") rose from GPT-5.1 on, per an OpenAI post-mortem reported second-hand.
- GPT-6 Astra (Graphite, September 2026): em dashes 88% below the human rate; "not simply" at 157 times the human rate, "rather than relying", "dependable", "another dimension", "together these".
- Claude, 3.5 to Opus 4.6 (2024 to early 2026): minimal structure and less bold than ChatGPT, "here", "according to", "based on", em dashes at roughly triple the human rate, long hedged multi-clause sentences, "you're absolutely right".
- Claude Opus 5 (2026): "deliberate" at 26 times the human rate, "every single" at 112, "rather than merely" at 160, "less like a X and more like a Y" at 105, plus "single most" and "arguably the most" (Graphite). An Arena comparison (August 2026, second-hand) found replies about three times as long as Opus 4.5's, sentences 58% longer, and more "load-bearing", "honestly", and "frankly". Anthropic's prompting guide says it runs long, with filler sections and redundant summaries, and narrates its own self-corrections.
- Claude Fable 5.1 and Opus 5.5 (2026): per Anthropic's guide, Fable 5.1 writes denser prose with longer sentences, fewer paragraph breaks, and less bold, fewer headers and lists, and can reproduce source passages without quotation marks; the guide gives "a dial worth turning" and "earns its keep" as its mannered prose. The Opus 5.5 system prompt (September 2026) asks for reports in prose, with lists written inline ("some things include: x, y, and z"), and at most one question per reply.
- Gemini, 2.5 era: verbose, corporate-flat, plain conversational vocabulary, more italics, list and header heavy, "[cite: 1]" leakage.
- Gemini 3.x (2026): 3.1 Pro has nearly stopped using em dashes and over-uses "incredibly", "profound", "furthermore the", "ultimately this", "this comprehensive guide", and "is not just a X, it is" (Graphite). The Gemini 3 Pro system prompt tells it to end on "Would you like me to …", so in Gemini text that closer is by design. The leaked 3.8 Flash prompt (September 2026) bans "Here's my take:", "Short answer:", and "Here are…".
- Grok, 2025 to 2026: superficially scientific vocabulary ("causal", "empirical", "correlate"), "X rather than Y" framing, and "underscore" long after other models dropped it. The leaked Grok 4.7 CLI prompt (September 2026) bans "X, not Y", "X rather than Y", "Bottom Line:", "delve", "foster", "leverage", "it's worth noting", self-answered questions, "This isn't about X. It's about Y.", and coined acronyms, so its vendor sees the same habits.
- DeepSeek: lenticular brackets and dagger marks leaking from its citation format, and curly quotes.
- Meta AI, Muse Spark (July 2026, leaked prompt): told to use no em dashes at all and to format with `- **Label**: explanation` bullets, headings, and tables. Bold-label bullets in its output are house style; see Mechanical bold and inline headers.
- Contractions: six 2026 models given identical prompts ranged from about 1,200 to over 30,000 contractions per million words. No contraction rate marks "AI" or "human"; see Human signals to preserve.

Em dashes per 1,000 words, measured in early 2026 (Freeburg) with no formatting instruction (rounded figures): GPT-5.4 at 1.4, below a human essay baseline of 3.2; Claude Opus 4.6 at 9.1 and DeepSeek V3 at 7.0, roughly triple it; Gemini 2.5 Pro at 3.5; Llama at zero. With a short instruction to avoid dashes, Claude Opus 4.6 fell to 0.2 and Gemini 2.5 Pro to zero, while GPT-4.1 barely moved (10.6 to 9.1). OpenAI cut the habit first. Later data is mixed: Graphite (September 2026, 10,000 web articles per model against 10,000 pre-ChatGPT human articles) puts Claude Opus 5 at about the human rate and Gemini 3.1 Pro near zero, while the Arena chat comparison found Opus 5 using 2.3 times as many as Opus 4.5. Articles and chat replies are different corpora, which probably explains the split, so date any figure you cite. Two secondary signals: machine em dashes are usually surrounded by spaces, and in scientific discussion sections a corpus study found em-dash prevalence rising from 4% of papers before ChatGPT to 20% in 2025. Neither is a single-document verdict, and neither is a reason to touch a dash in a writer's draft.

## False positives

Do not over-edit these without a cluster of other tells:

- polished grammar, formal vocabulary, dry prose
- one transition word, one dash, one curly quote
- a single instance of a focal word such as "delve" or "intricate"
- a single tricolon or one "not X but Y" antithesis
- one warm "happy to help" in a genuine message
- a common salutation or sign-off
- clean formatting from a CMS or document editor
- casual and formal register mixed in one piece, which fits technical writers, young writers, and neurodivergent writers; Wikipedia lists it as an ineffective indicator
- anything under about 200 words. Style classifiers lose most of their accuracy at that length, so a short message gets no stylometric verdict at all; only near-conclusive artefacts count

Why single features are unreliable, and why detector-evasion is a non-goal:

- Detectors vary enormously and the bias is documented. A 2023 Stanford study found more than half of non-native English essays misclassified as AI across seven detectors, on a sample of 179 essays. A 2026 ACL study of 16 detectors on about 41,700 essays confirmed the direction: essays by English language learners are more likely to be classified as machine-generated, and non-white learners more so than white ones. Human raters in the same study were no better than chance and showed no such bias. At the other end, commercial vendors report near-zero false-positive rates for their current products, figures that are vendor-relayed and unverified here. OpenAI retired its own classifier in 2023 after it correctly flagged only 26% of AI text. Light paraphrasing still defeats most detectors.
- Plain, predictable, low-variation prose is the normal style of fluent non-native and formal writers. Flagging it penalises people, not machines. The same is widely reported for neurodivergent writers, and at least one university finding has been annulled on that basis. A July 2026 preprint gives the first measurement: across about 33,000 Reddit posts, one older detector flagged posts from autism communities 25% more often than posts from general communities, and 50% more often at matched length, although the flagged posts were no flatter or more predictable. It is one detector, not peer-reviewed, and autism was inferred from the subreddit, so take the direction, not the rate. A 2025 Grammarly benchmark of about 208,000 document pairs found the same kind of gap for dialect, age, and register: four open-source detectors scored worst on African American English, Singlish, teen, and informal Gen Z writing.
- Detectors cannot tell a human draft lightly polished by a model from generated text. In a 2026 study all five detectors tested flagged a non-trivial share of LLM-polished peer reviews as AI-written, so any policy that allows polishing cannot be enforced by a detector. Watermarks do not settle it either: in a 2026 test of the open-source SynthID-Text implementation, meaning-preserving paraphrase removed 98% of the watermarks, and 5.4% of human text was flagged.
- "delve" is an RLHF artefact, not, as sometimes claimed, a marker of Nigerian English; corpus work found it does not originate there. It is common in fluent Nigerian, Indian, and other non-native business English. One or two focal words mean nothing; only a dense cluster in a short passage is a signal. Humans are also adopting these words: recordings of unscripted speech show "delve", "meticulous", and "underscore" rising since 2023, some more than doubling, so the 2023 list keeps losing power as a tell.
- The em dash is the least reliable single tell. See Dash dependence above.

Never strip a feature on a single signal. The job is to make the writing fit its purpose, not to make it pass a detector.

## Human signals to preserve

Preserve:

- specific, unusual details
- mixed feelings and unresolved tension
- dated or subculture-specific references
- first-person choices that fit the genre
- genuine asides and self-corrections
- varied sentence length
- plain repeated terms that improve clarity. Newer models avoid repeating a word near its last use, so a writer who says "the parser" four times in a paragraph is showing a human habit, not a flaw
- stance hedges and intensifiers: "I think", "probably", "very", "perhaps", "tends to"
- rhetorical questions. Humans use them at more than double the LLM rate; the tell is the scripted question-and-answer habit, not the question
- wordy constructions such as "in order to" and "as a result of"
- superlatives and definitive statements the writer is willing to stand behind
- simple "is" and "has" sentences and plain verbs ("wrote", not "authored")
- parenthetical asides and brackets. Model revision removes them, and current models use far fewer than human writers do
- exclamation marks where the writer uses them. Current models rarely write one in an article; the social-post tell is one on every line, not one in a piece
- concessives ("although", "though") and discourse particles ("well", "anyway", "mind you"), which a 2026 register study found models under-use
- the writer's own contraction rate, high or low. Rates vary about 25-fold between current models, so compare against the writer's sample, never against a supposed human rate
- a single em dash, a lone "delve", or one tricolon used naturally
