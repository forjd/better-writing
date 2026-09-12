#!/usr/bin/env python3
"""Validate repository invariants. Dependency-free; run from anywhere.

Checks:
- SKILL.md frontmatter: name format and length, description length,
  and that every references/ path it mentions exists.
- Each fixture in evals/fixtures/ has an input.md and a checks.json with a
  brief, at least one check, valid JSON, and compiling regexes, plus a
  known-good output in evals/examples/<fixture>.md (and no stray examples).
- Every symlink under skills/ resolves to a file inside the repo, and each
  tap directory contains a SKILL.md.
- Tap parity: every references/*.md and agents/*.yaml has a matching
  symlink in each tap, and no unexpected symlinks exist (allowlist is the
  mirrored top files README.md, LICENSE, CHANGELOG.md, SKILL.md plus
  references/*.md and agents/*.yaml, e.g. agents/openai.yaml).
- Tap content: each tap symlink is byte-identical to its root counterpart.
- agents/*.yaml schema: top-level name matches SKILL.md, version present,
  and default_prompt mentions the skill trigger.

Tap symlinks require a checkout with symlink support (git core.symlinks=true).
They survive `git clone` but not GitHub's Download ZIP or a Windows checkout
without symlink support; in those cases use the repo root, which is canonical.

Exits non-zero if any check fails.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

errors = []

KNOWN_VOICE_KEYS = {
    "contraction_rate",
    "first_person_rate",
    "hedge_rate",
    "mean_word_length",
}

# Top-level root files mirrored into each tap as symlinks.
EXPECTED_TOP_SYMLINKS = {"README.md", "LICENSE", "CHANGELOG.md", "SKILL.md"}


def check(condition, message):
    if not condition:
        errors.append(message)


def _strip_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_simple_frontmatter(block):
    """Minimal single-level YAML subset for SKILL.md frontmatter.

    Handles `key: value` with surrounding quotes stripped, and folded
    `>` / `|` blocks whose indented continuation lines are joined with a
    space (`>`) or newline (`|`). Other nested structures are out of scope;
    plain indented continuations are joined with a space.
    """
    data = {}
    current_key = None
    folded = None
    for raw_line in block.split("\n"):
        stripped = raw_line.strip()
        indented = raw_line.startswith(" ") or raw_line.startswith("\t")
        if folded and current_key is not None and (indented or stripped == ""):
            if stripped == "":
                continue
            if folded == ">":
                data[current_key] += (" " if data[current_key] else "") + stripped
            else:
                data[current_key] += ("\n" if data[current_key] else "") + stripped
            continue
        folded = None
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw_line)
        if not match:
            if current_key is not None and indented and stripped:
                data[current_key] += " " + stripped
            continue
        key, val = match.group(1), match.group(2).strip()
        current_key = key
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            data[key] = ""
            folded = val[0]
            continue
        data[key] = _strip_quotes(val)
    return data


def check_frontmatter():
    skill_path = ROOT / "SKILL.md"
    if not skill_path.is_file():
        errors.append("SKILL.md: missing file")
        return None
    try:
        raw = skill_path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"SKILL.md: unreadable ({exc})")
        return None
    # Normalize CRLF/CR to LF so the frontmatter match works cross-platform.
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Allow a missing trailing newline after the closing fence.
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.S)
    check(match, "SKILL.md: missing frontmatter block")
    if not match:
        return None
    frontmatter = parse_simple_frontmatter(match.group(1))

    name = frontmatter.get("name")
    check(name, "SKILL.md: frontmatter has no name")
    if name:
        check(
            re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name),
            f"SKILL.md: name {name!r} must be lowercase letters, digits, and hyphens",
        )
        check(len(name) <= 64, f"SKILL.md: name is {len(name)} characters, limit 64")

    desc = frontmatter.get("description")
    check(desc, "SKILL.md: frontmatter has no description")
    if desc:
        check(
            len(desc) <= 1024,
            f"SKILL.md: description is {len(desc)} characters, limit 1024",
        )

    for ref in sorted(set(re.findall(r"`(references/[A-Za-z0-9_./-]+\.md)`", text))):
        # Traversal guard: refs must stay inside references/.
        parts = Path(ref).parts
        if ".." in parts:
            errors.append(f"SKILL.md: mentions {ref} with parent traversal")
            continue
        check((ROOT / ref).is_file(), f"SKILL.md: mentions {ref} but it does not exist")

    return name


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_fixtures():
    fixtures_dir = ROOT / "evals" / "fixtures"
    examples_dir = ROOT / "evals" / "examples"
    missing = False
    if not fixtures_dir.is_dir():
        errors.append("evals/fixtures: missing directory")
        missing = True
    if not examples_dir.is_dir():
        errors.append("evals/examples: missing directory")
        missing = True
    if missing:
        return
    try:
        fixtures = sorted(p for p in fixtures_dir.iterdir() if p.is_dir())
    except OSError as exc:
        errors.append(f"evals/fixtures: unreadable ({exc})")
        return
    check(fixtures, "evals/fixtures: no fixtures found")

    for fixture in fixtures:
        rel = fixture.relative_to(ROOT)
        check((fixture / "input.md").is_file(), f"{rel}: missing input.md")
        check(
            (examples_dir / f"{fixture.name}.md").is_file(),
            f"evals/examples/{fixture.name}.md: missing known-good output",
        )

        checks_path = fixture / "checks.json"
        if not checks_path.is_file():
            errors.append(f"{rel}: missing checks.json")
            continue
        try:
            checks = json.loads(checks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}/checks.json: invalid JSON ({exc})")
            continue
        if not isinstance(checks, dict):
            errors.append(f"{rel}/checks.json: top level must be an object")
            continue

        brief = checks.get("brief")
        check(
            isinstance(brief, str) and brief.strip(),
            f"{rel}/checks.json: brief must be a non-empty string",
        )

        for key in ("required", "banned", "banned_regex"):
            if key in checks:
                value = checks[key]
                check(
                    isinstance(value, list)
                    and all(isinstance(item, str) for item in value),
                    f"{rel}/checks.json: {key} must be a list of strings",
                )

        for key in ("max_words_ratio", "min_words_ratio"):
            if key in checks:
                value = checks[key]
                check(
                    _is_number(value) and value > 0,
                    f"{rel}/checks.json: {key} must be a positive number",
                )

        if "voice_drift" in checks:
            drift = checks["voice_drift"]
            if not isinstance(drift, dict):
                errors.append(f"{rel}/checks.json: voice_drift must be an object")
            else:
                for dkey, dval in drift.items():
                    check(
                        dkey in KNOWN_VOICE_KEYS,
                        f"{rel}/checks.json: voice_drift has unknown key {dkey!r}",
                    )
                    if dkey in KNOWN_VOICE_KEYS:
                        check(
                            _is_number(dval),
                            f"{rel}/checks.json: voice_drift[{dkey}] must be numeric",
                        )

        check(
            checks.get("required")
            or checks.get("banned")
            or checks.get("banned_regex")
            or checks.get("max_words_ratio") is not None
            or checks.get("min_words_ratio") is not None
            or checks.get("voice_drift"),
            f"{rel}/checks.json: defines no required, banned, banned_regex, "
            "max/min_words_ratio, or voice_drift checks",
        )
        banned_regex = checks.get("banned_regex", [])
        if isinstance(banned_regex, list):
            for pattern in banned_regex:
                if not isinstance(pattern, str):
                    continue
                try:
                    re.compile(pattern)
                except re.error as exc:
                    errors.append(
                        f"{rel}/checks.json: banned_regex /{pattern}/ "
                        f"does not compile ({exc})"
                    )

    # Glob on a missing dir returns empty, but the dir guard above already
    # reported it; keep this graceful (no traceback if examples vanish).
    try:
        examples = sorted(examples_dir.glob("*.md"))
    except OSError:
        examples = []
    for example in examples:
        check(
            (fixtures_dir / example.stem).is_dir(),
            f"evals/examples/{example.name}: no matching fixture",
        )


def check_agents(expected_name=None):
    agents_dir = ROOT / "agents"
    if not agents_dir.is_dir():
        errors.append("agents: missing directory")
        return
    try:
        yamls = sorted(agents_dir.glob("*.yaml"))
    except OSError as exc:
        errors.append(f"agents: unreadable ({exc})")
        return
    check(yamls, "agents: no *.yaml found")
    for path in yamls:
        rel = path.relative_to(ROOT)
        try:
            raw = path.read_bytes().decode("utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{rel}: unreadable ({exc})")
            continue
        text = raw.replace("\r\n", "\n").replace("\r", "\n")
        # Top-level keys only (no leading indent).
        name_match = re.search(r"^name:\s*(.+?)\s*$", text, re.M)
        if not name_match:
            errors.append(f"{rel}: missing top-level name")
        else:
            agent_name = _strip_quotes(name_match.group(1))
            check(
                re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", agent_name),
                f"{rel}: name {agent_name!r} must be lowercase letters, "
                "digits, and hyphens",
            )
            if expected_name:
                check(
                    agent_name == expected_name,
                    f"{rel}: name {agent_name!r} does not match "
                    f"SKILL.md name {expected_name!r}",
                )
        version_match = re.search(r"^version:\s*(.+?)\s*$", text, re.M)
        check(version_match, f"{rel}: missing top-level version")
        if version_match and not _strip_quotes(version_match.group(1)):
            errors.append(f"{rel}: version must be a non-empty string")
        prompt_match = re.search(
            r"^[ \t]*default_prompt:\s*(.+?)\s*$", text, re.M)
        prompt_value = _strip_quotes(prompt_match.group(1)) if prompt_match else ""
        check(
            "$better-writing" in prompt_value or "/better-writing" in prompt_value,
            f"{rel}: default_prompt mentions neither $better-writing "
            "nor /better-writing",
        )


def check_tap():
    skills_dir = ROOT / "skills"
    if not skills_dir.is_dir():
        return
    references_dir = ROOT / "references"
    agents_dir = ROOT / "agents"
    expected_symlinks = []
    for tap in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        check(
            (tap / "SKILL.md").is_file(),
            f"{tap.relative_to(ROOT)}: tap has no SKILL.md",
        )
        # Parity: each tap mirrors the root references/*.md, agents/*.yaml,
        # and the top-level docs (README, LICENSE, CHANGELOG, SKILL.md).
        expected = set()
        for top in EXPECTED_TOP_SYMLINKS:
            if (ROOT / top).is_file():
                expected.add(tap / top)
        if references_dir.is_dir():
            for ref in sorted(references_dir.glob("*.md")):
                expected.add(tap / "references" / ref.name)
        if agents_dir.is_dir():
            for agent in sorted(agents_dir.glob("*.yaml")):
                expected.add(tap / "agents" / agent.name)
        expected_symlinks.extend(sorted(expected))
        for want in sorted(expected):
            rel = want.relative_to(ROOT)
            check(
                want.is_symlink(),
                f"{rel}: expected symlink to root counterpart "
                f"{want.relative_to(tap)} is missing (want "
                f"core.symlinks=true checkout)",
            )
        actual_symlinks = {
            p for p in tap.rglob("*") if p.is_symlink()
        }
        for extra in sorted(actual_symlinks - expected):
            errors.append(
                f"{extra.relative_to(ROOT)}: unexpected symlink "
                "(allowlist: README.md, LICENSE, CHANGELOG.md, SKILL.md, "
                "references/*.md, agents/*.yaml)"
            )
        # Byte-identical content: the tap file must match its root counterpart.
        for want in sorted(expected):
            if not want.is_symlink() or not want.exists():
                continue
            counterpart = ROOT / want.relative_to(tap)
            if not counterpart.is_file():
                continue
            try:
                same = want.read_bytes() == counterpart.read_bytes()
            except OSError as exc:
                errors.append(f"{want.relative_to(ROOT)}: unreadable ({exc})")
                continue
            check(
                same,
                f"{want.relative_to(ROOT)}: content differs from "
                f"{counterpart.relative_to(ROOT)} (stale copy or wrong target)",
            )
    for path in sorted(skills_dir.rglob("*")):
        if not path.is_symlink():
            continue
        rel = path.relative_to(ROOT)
        try:
            target = path.resolve()
        except OSError as exc:
            errors.append(f"{rel}: cannot resolve symlink ({exc})")
            continue
        try:
            link_target = path.readlink()
        except OSError:
            link_target = target
        check(path.exists(), f"{rel}: broken symlink -> {link_target}")
        try:
            inside = target.is_relative_to(ROOT)
        except AttributeError:  # Python < 3.9 fallback
            try:
                target.relative_to(ROOT)
                inside = True
            except ValueError:
                inside = False
        check(inside, f"{rel}: symlink escapes the repo -> {target}")
    # Best-effort git index check: tracked tap links must be mode 120000.
    # Skipped when git is unavailable (e.g. source tarball without .git).
    if expected_symlinks and (ROOT / ".git").exists():
        try:
            proc = subprocess.run(
                ["git", "-C", str(ROOT), "ls-files", "-s"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            proc = None
        if proc is not None and proc.returncode == 0:
            modes = {}
            for line in proc.stdout.splitlines():
                if "\t" not in line:
                    continue
                meta, fpath = line.split("\t", 1)
                parts = meta.split()
                if not parts:
                    continue
                modes[fpath] = parts[0]
            for want in expected_symlinks:
                rel_posix = want.relative_to(ROOT).as_posix()
                mode = modes.get(rel_posix)
                if mode is None:
                    errors.append(
                        f"{rel_posix}: not tracked in git "
                        "(expected symlink, mode 120000)"
                    )
                elif mode != "120000":
                    errors.append(
                        f"{rel_posix}: git mode {mode} != 120000 "
                        "(not a symlink; check core.symlinks=true and re-checkout)"
                    )


def main():
    skill_name = check_frontmatter()
    check_fixtures()
    check_agents(skill_name)
    check_tap()
    if errors:
        for message in errors:
            print(f"FAIL {message}")
        print(f"{len(errors)} problem(s) found")
        return 1
    print("all repo checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
