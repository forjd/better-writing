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

Exits non-zero if any check fails.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

errors = []


def check(condition, message):
    if not condition:
        errors.append(message)


def check_frontmatter():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    check(match, "SKILL.md: missing frontmatter block")
    if not match:
        return
    frontmatter = match.group(1)

    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.M)
    check(name_match, "SKILL.md: frontmatter has no name")
    if name_match:
        name = name_match.group(1).strip()
        check(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name),
              f"SKILL.md: name {name!r} must be lowercase letters, digits, and hyphens")
        check(len(name) <= 64, f"SKILL.md: name is {len(name)} characters, limit 64")

    desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.M)
    check(desc_match, "SKILL.md: frontmatter has no description")
    if desc_match:
        desc = desc_match.group(1).strip()
        check(len(desc) <= 1024, f"SKILL.md: description is {len(desc)} characters, limit 1024")

    for ref in sorted(set(re.findall(r"`(references/[a-z0-9-]+\.md)`", text))):
        check((ROOT / ref).is_file(), f"SKILL.md: mentions {ref} but it does not exist")


def check_fixtures():
    fixtures_dir = ROOT / "evals" / "fixtures"
    examples_dir = ROOT / "evals" / "examples"
    fixtures = sorted(p for p in fixtures_dir.iterdir() if p.is_dir())
    check(fixtures, "evals/fixtures: no fixtures found")

    for fixture in fixtures:
        rel = fixture.relative_to(ROOT)
        check((fixture / "input.md").is_file(), f"{rel}: missing input.md")
        check((examples_dir / f"{fixture.name}.md").is_file(),
              f"evals/examples/{fixture.name}.md: missing known-good output")

        checks_path = fixture / "checks.json"
        if not checks_path.is_file():
            errors.append(f"{rel}: missing checks.json")
            continue
        try:
            checks = json.loads(checks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}/checks.json: invalid JSON ({exc})")
            continue

        check("brief" in checks, f"{rel}/checks.json: missing brief")
        check(checks.get("required") or checks.get("banned") or checks.get("banned_regex"),
              f"{rel}/checks.json: defines no required, banned, or banned_regex checks")
        for pattern in checks.get("banned_regex", []):
            try:
                re.compile(pattern)
            except re.error as exc:
                errors.append(f"{rel}/checks.json: banned_regex /{pattern}/ does not compile ({exc})")

    for example in sorted(examples_dir.glob("*.md")):
        check((fixtures_dir / example.stem).is_dir(),
              f"evals/examples/{example.name}: no matching fixture")


def check_tap():
    skills_dir = ROOT / "skills"
    if not skills_dir.is_dir():
        return
    for tap in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        check((tap / "SKILL.md").is_file(),
              f"{tap.relative_to(ROOT)}: tap has no SKILL.md")
    for path in sorted(skills_dir.rglob("*")):
        if not path.is_symlink():
            continue
        rel = path.relative_to(ROOT)
        target = path.resolve()
        check(path.exists(), f"{rel}: broken symlink -> {path.readlink()}")
        check(target.is_relative_to(ROOT),
              f"{rel}: symlink escapes the repo -> {target}")


def main():
    check_frontmatter()
    check_fixtures()
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
