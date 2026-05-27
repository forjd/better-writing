<div align="center">

# Better Writing

An agent skill for prose that sounds clear, specific, and human.

[![Agent Skill](https://img.shields.io/badge/agent%20skill-better--writing-2563eb?style=for-the-badge)](./SKILL.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-111827?style=for-the-badge)](./LICENSE)
[![skills.sh](https://skills.sh/b/forjd/better-writing)](https://skills.sh/forjd/better-writing)

</div>

## What It Is

Better Writing is an agent skill for rewriting, drafting, and reviewing prose. It helps agents remove generic AI tells, sharpen vague claims, preserve voice, and choose the right level of polish for the audience.

It is not a grammar-only pass. It is a context-aware writing editor with checks for:

- AI-sounding patterns such as significance inflation, vague attribution, promotional padding, and formulaic conclusions
- slop structures such as throat-clearing, binary contrast, false agency, and manufactured drama
- voice calibration from user-provided samples
- factual guardrails so specificity does not turn into invention
- a final pre-flight check before delivery

## When To Use It

Use this skill when an agent needs to improve:

- emails and messages
- essays, posts, and opinion drafts
- reports, proposals, and memos
- documentation and release notes
- marketing copy and product copy
- UI text and microcopy
- any draft that sounds too generic, verbose, evasive, salesy, or AI-written

## Installation

The [skills.sh CLI](https://www.skills.sh/docs/cli) is the easiest way to install the skill once the repository is public.

With `npx`:

```bash
npx skills add forjd/better-writing
```

With `bunx`:

```bash
bunx skills add forjd/better-writing
```

You can also install from the full GitHub URL:

```bash
npx skills add https://github.com/forjd/better-writing
bunx skills add https://github.com/forjd/better-writing
```

For local development, install from this checkout:

```bash
npx skills add /path/to/better-writing
bunx skills add /path/to/better-writing
```

The CLI collects anonymous install telemetry by default. To opt out:

```bash
DISABLE_TELEMETRY=1 npx skills add forjd/better-writing
DISABLE_TELEMETRY=1 bunx skills add forjd/better-writing
```

You can also copy the folder into your agent skills directory if your agent runtime supports local skill discovery.

## Usage

Invoke it explicitly:

```text
Use $better-writing to rewrite this launch email so it sounds direct, warm, and less AI-written.
```

Or ask for the behaviour naturally:

```text
Humanise this draft without making it casual. Keep the legal caveats intact.
```

```text
Review this landing-page copy for generic AI writing and give me a sharper version.
```

```text
Use my writing sample below as the voice reference, then rewrite the article intro.
```

## What Is Inside

```text
better-writing/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
`-- references/
    |-- ai-writing-patterns.md
    |-- preflight.md
    |-- sources.md
    |-- structures-and-phrases.md
    `-- voice-and-context.md
```

`SKILL.md` stays concise so agents can load it quickly. The detailed audit material lives in `references/` and is loaded only when needed.

## Design Principles

- Specific beats impressive.
- Direct beats announced.
- Context beats blanket rules.
- Voice beats cleanliness.
- Evidence beats authority theatre.
- Trust the reader.

## Validation

Validate the skill with the standard skill creator checker:

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py /path/to/better-writing
```

This checks the required skill metadata and naming rules.

## Influences

Better Writing merges ideas from:

- [blader/humanizer](https://github.com/blader/humanizer)
- [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)
- [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)
- [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)

See [references/sources.md](./references/sources.md) for source notes.

## Contributing

Keep the skill lean. Put core workflow guidance in [SKILL.md](./SKILL.md), and move detailed pattern lists or examples into [references/](./references/).

Before opening a pull request:

1. Run the skill validator.
2. Check that new prose uses British English.
3. Avoid adding bulky documentation that the agent does not need.
4. Keep examples factual, concise, and easy to audit.

## Licence

MIT licence. Copyright (c) 2026 Forjd.
