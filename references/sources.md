# Sources

This skill is a new synthesis informed by these public sources:

- `blader/humanizer`: https://github.com/blader/humanizer
  AI-writing pattern taxonomy, voice calibration, false-positive caution, and draft-audit-final loop.
- `hardikpandya/stop-slop`: https://github.com/hardikpandya/stop-slop
  Sharper anti-slop checks for throat-clearing, binary contrast, false agency, filler phrases, and rhythm.
- `Leonxlnx/taste-skill`: https://github.com/Leonxlnx/taste-skill
  Context-first brief reading, explicit quality dials, anti-default discipline, and pre-flight matrices.
- `cursor/plugins` (`pstack/skills/unslop`): https://github.com/cursor/plugins/blob/main/pstack/skills/unslop/SKILL.md
  Abstract metaphor nouns, the mechanism-not-mood rule and its swap test, colon-as-connector, the redundancy reading of inline-header bullets, and the reminder that voiceless prose is its own tell. That last one came from its "Adding soul" section, which PR #329 removed on 2026-09-07; the credit is to the earlier version. The same PR added the over-compression rule.
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

## 2026-09-01 research refresh

These informed the hedging re-scope, the corrected dash and fingerprint entries, the detector-bias update, and the Tier 1 promotion of binary contrast.

- Jiang and Hyland, "Rhetorical distinctions", English for Specific Purposes 79, 2025.
  ChatGPT essays show significantly less interactional metadiscourse (hedges, boosters, attitude markers) than human essays; the basis for treating stance hedges and intensifiers as human signals.
- Bakhshi, "Saying More Than They Know", arXiv 2604.19768, 2026.
  Tricolons at nearly twice the expert rate, performed hesitancy at twice the human density, rhetorical questions used by humans at more than double the LLM rate.
- Freeburg, "The Last Fingerprint", arXiv 2603.27006, 2026.
  Em dashes per 1,000 words by model (GPT-5.4 1.43, Claude Opus 4.6 9.09, DeepSeek V3 6.95, Gemini 2.5 Pro 3.53, human baseline 3.23 from eight essays).
- Czuma, "Em-ergence of the em-dash", arXiv 2606.29540, 2026.
  Pre-registered medRxiv study: em-dash prevalence in discussion sections rose from 4.23% pre-ChatGPT to 20.3% in 2025.
- Sun et al., "Idiosyncrasies in Large Language Models", ICML 2025.
  Per-vendor lexical fingerprints; Claude marked by minimal structure and less bold than ChatGPT.
- Milička, Marklová, Cvrček, "Benchmark of stylistic variation", arXiv 2509.10179, 2025.
  Biber multidimensional analysis over 16 models: instruction tuning drives the shared tells and models from one vendor do not cluster.
- Stowe et al., "Identifying Bias in Machine-generated Text Detection", ACL 2026.
  16 detectors, about 41,700 essays: English language learners over-flagged, non-white learners more so; human annotators near chance with no bias. Notes Liang 2023 rested on 179 essays.
- Anderson, Galpin, Juzek, AIES 2025, and Matsui, Perspectives on Medical Education, 2025.
  Humans adopting "delve", "meticulous", "underscore" in unscripted speech and medical writing since 2023.
- Rudnicka, Scientific American, July 2025, and iMEdD, January 2026.
  ChatGPT and Grammarly both remove "in order to"; the basis for treating wordy constructions as a human signal.
- Oremus, The Atlantic, July 2026 (via Wikipedia's Negative parallelism entry; not read directly).
  Negative parallelism at about three times the human rate, rising in corporate filings. Second-hand until someone reads the article.
- Anthropic, Claude Fable 5.1 system prompt and prompting guides, 2026: https://platform.claude.com/docs/en/release-notes/system-prompts/claude-fable-5-1
  "genuinely", "honestly", "straightforward" as disingenuous sincerity modifiers; the "mannered prose" definition.
- blader/humanizer v2.10 to v2.11 (2026): https://github.com/blader/humanizer
  Shadowboxing, phantom alternatives, the editorial scar-tissue test (PR #207), speculation from absence, hyphenated pairs, heading restated by its first sentence, casual-register signposting (PR #219).
- asavvin-pixel/unslop (2026): https://github.com/asavvin-pixel/unslop
  Aphorism budget, stating the moral, invented baselines, the outline test, slack, and the observation that cleaned GPT-isms leave uniform confidence and template-shaped structure behind.
- hardikpandya/stop-slop: the pull-quote test.
- Kendro, Maloney, Jarvis, International Journal of Applied Linguistics, 2025 (doi 10.1111/ijal.70115).
  Lexical dispersion as the strongest predictor across six diversity measures; the close-repetition-avoidance habit strengthens in newer ChatGPT versions.
- Gude et al., "More Aligned, Less Diverse?", arXiv 2605.06030, 2026.
  2025 instruction-tuned models write sentences 15 to 30% longer than humans and over-use nominal modification and participial phrases.
- Russell et al., "StoryScope", arXiv 2604.03136, 2026.
  61,608 stories: AI stories state the moral (77% vs 52%) and render emotion through body metaphor (81% vs 38%).
- Masrour, Emi, Spero, "DAMAGE", GenAIDetect at COLING 2025, and Pangram Labs, "How well does Pangram perform on humanizers?", August 2025.
  19 commercial humanisers all degraded the original; tortured phrases and non-standard Unicode as residue.
- Wiki Education, January 2026: 178 of 3,078 reviewed articles flagged; 7% cited a fabricated source, over two-thirds failed verification.
- Williams and Bizup, Style: Lessons in Clarity and Grace; Pinker, The Sense of Style; Zinsser, On Writing Well; Klinkenborg, Several Short Sentences About Writing; Orwell, Politics and the English Language; Graham, "Write like you talk"; Saunders, Story Club.
  The sentence-craft checks: characters as subjects, old before new, the stress position, cohesion, the curse-of-knowledge pass, connectors only where order fails, the talk test, the per-sentence pass, and the stock-phrase diagnostic.
- Gorrie, "Leave the em-dash alone", Dead Language Society, 2025: https://www.deadlanguagesociety.com/p/em-dash-ai-writing-panic
  "AI prose has no sense of proportion"; the one-emphasised-sentence rule.
- "Catch Me If You Can? Not Yet", EMNLP 2025 Findings, arXiv 2509.14543, and "Authorship impersonation via LLM prompting does not evade verification", arXiv 2603.29454.
  Few-shot imitation copies surface features and fails on blogs and forums; lexical and syntactic features identify a writer. The basis for measure, edit less, measure again.
- van Nuenen, "Voice Under Revision", arXiv 2604.22142, 2026.
  Rewrites cut contractions, first person, and function words and raise word length even under a voice-preserving prompt (32% smaller effect, same direction). The basis for the voice check and the eval metrics.
- Biber, Dimensions of English (Bamberg summary) and Basecamp, "How we communicate".
  Involved versus informational markers per medium; the chat register.
- River, "How ghostwriters capture client voice", and the ghost-writer skills by angelarose210, robertguss, gncll, and dannwaneri.
  Sample size, negative samples, forbidden patterns, and the measured profile.
- Paech, "Antislop", ICLR 2026, arXiv 2510.15061, and https://github.com/sam-paech/slop-score
  Over-representation ratios for LLM fiction vocabulary (some phrases at over a thousand times the human rate); the not-x-but-y weighting behind the eval contrast checks.
- Wikipedia:Signs of AI writing, fetched 2026-09-01.
  Current vocabulary eras, the spaced-dash note, the Grok entries, and the "signs of human writing" list.

## 2026-09-22 research refresh

These informed the corrected dash and fingerprint entries, the new leaked artefacts, the detector-bias and short-text guardrails, the new human signals, the change-note rule, the scope-word preflight check, and the eval additions (split-contrast check, `mattr` and `sentence_length_sd`, the `ranking-claims` fixture, and the human corpus). Leaked system prompts are unofficial; items marked second-hand were not read directly.

- Chambers and Kelley, "The misclassification of autistic writing as AI-generated", arXiv 2607.14729, 2026 (preprint).
  About 33,000 Reddit posts, one detector: posts from autism communities flagged 25% more often, 50% at matched length, with no lower perplexity or burstiness.
- Basu, Zhang, Raheja, "BAID", arXiv 2512.11505, 2025.
  About 208,000 document pairs, four open-source detectors: worst results on African American English, Singlish, teen, and informal Gen Z writing.
- Saha et al., arXiv 2603.20450, 2026; Ren, Raghavan, Garg, arXiv 2606.25152, 2026.
  All five detectors misclassified a share of LLM-polished reviews as AI-written; a commercial detector reached 24% accuracy on adversarially humanised text.
- Tamim and Khan, arXiv 2607.16010, 2026.
  Paraphrase removed 98.3% of SynthID-Text watermarks in the open-source MarkLLM implementation, with a 5.4% false-positive rate on human text.
- Freeburg, "The Last Fingerprint", arXiv 2603.27006, 2026 (full text).
  The suppression condition: a short no-dash instruction takes Claude Opus 4.6 from 9.09 to 0.19 per 1,000 words and Gemini 2.5 Pro to zero; GPT-4.1 moves from 10.62 to 9.10.
- Baumler et al., "Can You Make It Sound Like You?", ACL 2026, arXiv 2604.24444; Maier, Zaiss, Bayer, arXiv 2605.02620, 2026.
  Post-edited text stays closer to LLM style than to the writer's own while writers feel it is theirs; replicated with GPT-5.5 and Opus 4.7 agents.
- Sourati et al., "The Shrinking Landscape of Linguistic Diversity", Nature Human Behaviour, 2026, doi 10.1038/s41562-026-02550-0.
  LLM revision cuts variance in writing complexity across writers by 21 to 50%.
- Chen et al., Digital Scholarship in the Humanities, 2026, doi 10.1093/llc/fqag064; El Attar et al., arXiv 2606.04177, 2026.
  Function-word classifiers above 95% on essays fall off sharply at 200 words; across 284 features, 27 models, and 10 domains only lexical richness held up. The basis for the short-text guardrail and the `mattr` marker.
- Rudnicka and Juzek, "Beyond 'AI Language'", arXiv 2608.06589, 2026; Rallapalli et al., arXiv 2604.14111, 2026.
  Contraction rates across six 2026 models from about 1,200 to over 30,000 per million words; LLMs under-use concessives and discourse particles.
- Miletić and Falk, arXiv 2605.19936, 2026.
  LLM-revised scientific text carries more commas and dashes and fewer brackets.
- Yakura et al., arXiv 2409.01754 v4, 2026; Geng and Trotta, arXiv 2502.09606, 2025; Kousha and Thelwall, arXiv 2509.09596, 2025.
  A preregistered experiment showing chatbot exposure causes vocabulary adoption; "delve" falling in arXiv abstracts once publicised; "underscore" in nearly half of 2024 PMC papers that use any LLM-associated term.
- Graphite, "AI Tells" (Druck, Paredes, Smith), September 2026: https://graphite.io/five-percent/research/ai-tells
  10,000 pre-ChatGPT human articles against 10,000 web articles per model; the Claude Opus 5, GPT-6 Astra, and Gemini 3.1 Pro phrase multiples and dash rates. A vendor study of web articles.
- Arena.ai, Claude Opus 5 style comparison, August 2026 (second-hand, via AlphaSignal and paddo.dev); The Economist, 30 July 2026 (second-hand); OpenAI, "Where the goblins came from", April 2026 (second-hand).
- Anthropic, "Prompting Claude Opus 5", "Prompting Claude Fable 5.1", and the Claude Opus 5.5 system prompt, read 2026-09-22.
- asgeirtj/system_prompts_leaks: https://github.com/asgeirtj/system_prompts_leaks
  Leaked GPT-5.5 Thinking, GPT-5.6, Gemini 3 Pro and 3.8 Flash, Grok 4.7, and Meta AI Muse Spark prompts. Unofficial; used only for what a vendor told its model to avoid or use.
- lidge-jun/opencodex issue #3150, 2026-09-01: the `citeturn…` token wrapped in private-use characters.
- blader/humanizer v3.0.0, 2026-09-06: https://github.com/blader/humanizer/releases/tag/v3.0.0
  The scope-word preservation check (PRs #236, #264), the split and clipped contrast forms, and the manufactured-gravity items (PR #240).
- tbhb/vale-ai-tells v1.37.0, 2026-09-15: https://github.com/tbhb/vale-ai-tells
  Announced counts, pseudo-clefts, shell nouns, comparisons with no second term, universal objects, spec-sheet negation, personified placement verbs, and the method behind the human corpus: count a candidate against pre-2022 human prose before making it a rule.
- Wikipedia:Signs of AI writing, fetched 2026-09-22 (revision 1376018375), and its talk page.
  The em-dash historical-indicator notice, elegant variation moved to historical indicators, false ranges dropped, change notes that list what was preserved, mixed register as an ineffective indicator, the new tracking parameters and Grok and Perplexity markup, markdown pipe tables, curly quotes by vendor, and the commit-speak preamble.

## 2026-09-25 research refresh

These informed the draft-from-scratch substance step, rewrite-not-patch, the detector-request guardrail, zero-width residue, the updated detector and expert-reader evidence, voice markers at their natural rate, and the contrast budget. All came via a September 2026 research summary and were not read directly.

- Jabarian and Imas, "Artificial Writing and Automated Detection", NBER Working Paper 34223, August 2025: https://www.nber.org/papers/w34223
  1,992 human passages in six genres against four 2025 models: the leading trained classifier near-zero error, robust even on stubs of 50 words or fewer (abstract read directly, 2026-09-25).
- Van Vlasselaer, Van Droogenbroeck, Spruyt, "Who wrote this?", International Journal for Educational Integrity, June 2026: https://link.springer.com/article/10.1007/s40979-026-00226-w
  160 documents, four detectors; false positives rare on human text by non-native writers, weaker tools under-counting AI content from the newest model.
- Russell, Karpinska, Iyyer, "People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text", ACL 2025: https://aclanthology.org/2025.acl-long.267/
  Five-reader majority vote misclassified 1 of 300 articles; cues included formality, originality, and clarity as well as vocabulary.
- Jakesch, Hancock, Naaman, "Human heuristics for AI-generated language are flawed", PNAS 2023: https://arxiv.org/abs/2206.07271
  Lay readers near chance, relying on cues such as first person.
- Saha and Feizi, "Almost AI, Almost Human", ACL Findings 2025: https://arxiv.org/abs/2502.15666
  Minimal polishing of human text flagged at 10 to 75% depending on the detector.
- Spinner, "How to generate AI drafts that sound more human", Wondering About AI, July 2026: https://wonderingaboutai.substack.com/p/how-to-generate-ai-drafts-that-sound
  Voice markers applied at their natural rate and never all at once; a patched sentence keeps the AI rhythm.
- Carter, "4 reasons your writing accidentally sounds AI-generated", PR Daily: https://www.prdaily.com/4-reasons-your-writing-accidentally-sounds-ai-generated-and-how-to-fix-it/
  Negative parallelism once per piece at most.
- Turnitin AI bypasser detection, 27 August 2025; Krishna et al., "Paraphrasing evades detectors", NeurIPS 2023: https://arxiv.org/abs/2303.13408
  Detectors trained against humanisers; character-level and paraphrase evasion.

Use these sources as diagnostic inspiration. Do not copy upstream examples or prose into user deliverables. When maintaining this skill, keep `SKILL.md` concise and move detailed pattern lists into references.
