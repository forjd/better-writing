#!/usr/bin/env python3
"""Validate repository invariants. Dependency-free; run from anywhere.

The skill lives in skills/better-writing/ (SKILL_DIR); paths below are
relative to it unless they start with evals/, skills/ or .claude-plugin/.

Checks:
- SKILL.md frontmatter: name format and length, description length,
  and that every references/ path it mentions exists.
- Each fixture in evals/fixtures/ has an input.md and a checks.json with a
  brief, at least one check, valid JSON, and compiling regexes, plus a
  known-good output in evals/examples/<fixture>.md (and no stray examples).
- evals/triggers.json holds non-empty should_trigger and should_not_trigger
  lists of {id, prompt}, with unique slug ids.
- Layout: no SKILL.md, references/ or agents/ at the repo root, and no
  symlinks under skills/, on disk or in the git index.
- The skill folder's LICENSE is byte-identical to the root LICENSE.
- agents/*.yaml schema: top-level name matches SKILL.md, version present,
  and default_prompt mentions the skill trigger.
- Release version: SKILL.md metadata.version is semver and matches every
  agents/*.yaml version and the release-please manifest, once it has one.
- Claude Code plugin: .claude-plugin/plugin.json and marketplace.json parse,
  their names match SKILL.md, and their versions match metadata.version.

Exits non-zero if any check fails.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Relative to ROOT, so tests that patch ROOT move the skill with it.
SKILL_DIR = Path("skills", "better-writing")
SKILL_MD = (SKILL_DIR / "SKILL.md").as_posix()

errors = []

CHECK_KEYS = {
    "name", "brief", "required", "required_regex", "banned", "banned_regex",
    "max_words_ratio", "min_words_ratio", "voice_drift", "mode",
    "max_copied_words",
}

# Below this, a change tuned on dev can overfit without the held-out
# numbers showing it (issue #42).
MIN_HELDOUT = 8

KNOWN_VOICE_KEYS = {
    "contraction_rate",
    "first_person_rate",
    "hedge_rate",
    "mean_word_length",
    "mattr",
    "sentence_length_sd",
}

# Where the skill lived before 2.0.0. None of these may come back.
OLD_ROOT_PATHS = ("SKILL.md", "references", "agents")
# Root files the skill folder ships a copy of.
SKILL_COPIES = ("LICENSE",)


def check(condition, message):
    if not condition:
        errors.append(message)


def skill_root():
    return ROOT / SKILL_DIR


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
    skill_path = skill_root() / "SKILL.md"
    if not skill_path.is_file():
        errors.append(f"{SKILL_MD}: missing file")
        return None
    try:
        raw = skill_path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"{SKILL_MD}: unreadable ({exc})")
        return None
    # Normalize CRLF/CR to LF so the frontmatter match works cross-platform.
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Allow a missing trailing newline after the closing fence.
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.S)
    check(match, f"{SKILL_MD}: missing frontmatter block")
    if not match:
        return None
    frontmatter = parse_simple_frontmatter(match.group(1))

    name = frontmatter.get("name")
    check(name, f"{SKILL_MD}: frontmatter has no name")
    if name:
        check(
            re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name),
            f"{SKILL_MD}: name {name!r} must be lowercase letters, digits, and hyphens",
        )
        check(len(name) <= 64, f"{SKILL_MD}: name is {len(name)} characters, limit 64")

    desc = frontmatter.get("description")
    check(desc, f"{SKILL_MD}: frontmatter has no description")
    if desc:
        check(
            len(desc) <= 1024,
            f"{SKILL_MD}: description is {len(desc)} characters, limit 1024",
        )

    for ref in sorted(set(re.findall(r"`(references/[A-Za-z0-9_./-]+\.md)`", text))):
        # Traversal guard: refs must stay inside references/.
        parts = Path(ref).parts
        if ".." in parts:
            errors.append(f"{SKILL_MD}: mentions {ref} with parent traversal")
            continue
        check((skill_root() / ref).is_file(),
              f"{SKILL_MD}: mentions {ref} but it does not exist")

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

        unknown = sorted(set(checks) - CHECK_KEYS)
        check(
            not unknown,
            f"{rel}/checks.json: unknown keys {unknown} (a misspelled key "
            "silently disables its check)",
        )

        brief = checks.get("brief")
        check(
            isinstance(brief, str) and brief.strip(),
            f"{rel}/checks.json: brief must be a non-empty string",
        )

        for key in ("required", "required_regex", "banned", "banned_regex"):
            if key in checks:
                value = checks[key]
                check(
                    isinstance(value, list)
                    and all(isinstance(item, str) and item.strip()
                            for item in value),
                    f"{rel}/checks.json: {key} must be a list of non-empty "
                    "strings",
                )

        for key in ("max_words_ratio", "min_words_ratio"):
            if key in checks:
                value = checks[key]
                check(
                    _is_number(value) and value > 0,
                    f"{rel}/checks.json: {key} must be a positive number",
                )

        if "mode" in checks:
            check(
                checks["mode"] in ("rewrite", "draft", "review"),
                f"{rel}/checks.json: mode must be rewrite, draft, or review",
            )

        if "max_copied_words" in checks:
            value = checks["max_copied_words"]
            check(
                isinstance(value, int) and not isinstance(value, bool)
                and value > 0,
                f"{rel}/checks.json: max_copied_words must be a positive "
                "integer",
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
            or checks.get("required_regex")
            or checks.get("banned")
            or checks.get("banned_regex")
            or checks.get("max_words_ratio") is not None
            or checks.get("min_words_ratio") is not None
            or checks.get("voice_drift")
            or checks.get("max_copied_words") is not None,
            f"{rel}/checks.json: defines no required, required_regex, banned, "
            "banned_regex, "
            "max/min_words_ratio, voice_drift, or max_copied_words checks",
        )
        for key in ("required_regex", "banned_regex"):
            patterns = checks.get(key, [])
            if not isinstance(patterns, list):
                continue
            for pattern in patterns:
                if not isinstance(pattern, str):
                    continue
                if not pattern.strip():
                    # An empty pattern matches every rewrite: a required one
                    # always passes and a banned one always fails.
                    errors.append(f"{rel}/checks.json: {key} has an empty pattern")
                    continue
                try:
                    re.compile(pattern)
                except re.error as exc:
                    errors.append(
                        f"{rel}/checks.json: {key} /{pattern}/ "
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


def check_splits():
    """evals/splits.json must partition every fixture into dev and heldout.

    The dev set is for tuning; heldout is read once for confirmation, so a
    fixture that drifts between the sets (or sits in neither) silently
    breaks the independence the split exists to protect.
    """
    splits_path = ROOT / "evals" / "splits.json"
    fixtures_dir = ROOT / "evals" / "fixtures"
    try:
        fixtures = sorted(p.name for p in fixtures_dir.iterdir() if p.is_dir())
    except OSError:
        fixtures = []
    try:
        splits = json.loads(splits_path.read_text(encoding="utf-8"))
    except OSError:
        errors.append("evals/splits.json: missing file")
        return
    except ValueError as exc:
        errors.append(f"evals/splits.json: invalid JSON ({exc})")
        return
    if not isinstance(splits, dict):
        errors.append("evals/splits.json: top level must be an object")
        return
    for key in ("dev", "heldout"):
        value = splits.get(key)
        check(isinstance(value, list) and value,
              f"evals/splits.json[{key!r}] must be a non-empty list of names")
        if isinstance(value, list):
            check(all(isinstance(n, str) and n for n in value),
                  f"evals/splits.json[{key!r}] must hold non-empty strings")
            if all(isinstance(n, str) for n in value):
                check(len(set(value)) == len(value),
                      f"evals/splits.json[{key!r}] lists a fixture twice")
    unknown = sorted(set(splits) - {"dev", "heldout"})
    check(not unknown,
          f"evals/splits.json: unknown keys {unknown} (known: dev, heldout)")
    for key in ("dev", "heldout"):
        value = splits.get(key)
        if not (isinstance(value, list)
                and all(isinstance(n, str) and n for n in value)):
            # Shape already reported above; set() below needs strings, so
            # stop here instead of crashing on unhashable entries.
            return
    dev, heldout = set(splits["dev"]), set(splits["heldout"])
    check(len(heldout) >= MIN_HELDOUT,
          f"evals/splits.json: heldout has {len(heldout)} fixtures, needs at "
          f"least {MIN_HELDOUT} (move new fixtures there, not dev ones)")
    overlap = sorted(dev & heldout)
    check(not overlap,
          f"evals/splits.json: {overlap} in both dev and heldout")
    covered = sorted(dev | heldout)
    check(covered == fixtures,
          "evals/splits.json: dev + heldout must cover every fixture exactly "
          f"once (fixtures: {fixtures}, covered: {covered})")


def check_triggers():
    """evals/triggers.json must hold two non-empty sets of {id, prompt}.

    run_triggers.py reports each set as its own rate, so an empty set or a
    duplicate id would quietly change what the rate means.
    """
    path = ROOT / "evals" / "triggers.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        errors.append("evals/triggers.json: missing file")
        return
    except ValueError as exc:
        errors.append(f"evals/triggers.json: invalid JSON ({exc})")
        return
    sets = ("should_trigger", "should_not_trigger")
    if not isinstance(data, dict):
        errors.append("evals/triggers.json: top level must be an object")
        return
    unknown = sorted(set(data) - set(sets))
    check(not unknown,
          f"evals/triggers.json: unknown keys {unknown} (known: {', '.join(sets)})")
    seen = set()
    for key in sets:
        cases = data.get(key)
        if not (isinstance(cases, list) and cases):
            errors.append(f"evals/triggers.json[{key!r}] must be a non-empty list")
            continue
        for index, case in enumerate(cases):
            where = f"evals/triggers.json[{key!r}][{index}]"
            if not (isinstance(case, dict) and set(case) == {"id", "prompt"}):
                errors.append(f"{where} must be an object with exactly id and prompt")
                continue
            case_id, prompt = case["id"], case["prompt"]
            if not (isinstance(case_id, str)
                    and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", case_id)):
                errors.append(f"{where}: id must be a lowercase-hyphenated slug")
                continue
            check(case_id not in seen, f"{where}: duplicate id {case_id!r}")
            seen.add(case_id)
            check(isinstance(prompt, str) and prompt.strip(),
                  f"{where}: prompt must be a non-empty string")


def check_version():
    """Return SKILL.md metadata.version, which release-please bumps."""
    try:
        raw = (skill_root() / "SKILL.md").read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None  # check_frontmatter already reported it
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    block = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.S)
    # metadata's children share the first child's indent; anything deeper
    # (metadata.release.version) is not metadata.version.
    match = block and re.search(
        r"^metadata:[ \t]*\n([ \t]+)(?:\S.*\n(?:\1[ \t]+.*\n)*\1)*?"
        r"version:\s*(.+?)\s*(?:#.*)?$",
        block.group(1) + "\n",
        re.M,
    )
    check(match, f"{SKILL_MD}: frontmatter has no metadata.version")
    if not match:
        return None
    version = _strip_quotes(match.group(2))
    check(
        re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version),
        f"{SKILL_MD}: metadata.version {version!r} is not MAJOR.MINOR.PATCH",
    )
    manifest_path = ROOT / ".release-please-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f".release-please-manifest.json: unreadable ({exc})")
        return version
    released = manifest.get(".")
    if released:
        check(
            released == version,
            f"{SKILL_MD}: metadata.version {version!r} does not match "
            f"release manifest {released!r}",
        )
    return version


def check_agents(expected_name=None, expected_version=None):
    agents_dir = skill_root() / "agents"
    label = (SKILL_DIR / "agents").as_posix()
    if not agents_dir.is_dir():
        errors.append(f"{label}: missing directory")
        return
    try:
        yamls = sorted(agents_dir.glob("*.yaml"))
    except OSError as exc:
        errors.append(f"{label}: unreadable ({exc})")
        return
    check(yamls, f"{label}: no *.yaml found")
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
        version_match = re.search(r"^version:\s*(.+?)\s*(?:#.*)?$", text, re.M)
        check(version_match, f"{rel}: missing top-level version")
        agent_version = _strip_quotes(version_match.group(1)) if version_match else ""
        if version_match and not agent_version:
            errors.append(f"{rel}: version must be a non-empty string")
        if expected_version and agent_version:
            check(
                agent_version == expected_version,
                f"{rel}: version {agent_version!r} does not match "
                f"SKILL.md metadata.version {expected_version!r}",
            )
        prompt_match = re.search(
            r"^[ \t]*default_prompt:\s*(.+?)\s*$", text, re.M)
        prompt_value = _strip_quotes(prompt_match.group(1)) if prompt_match else ""
        check(
            "$better-writing" in prompt_value or "/better-writing" in prompt_value,
            f"{rel}: default_prompt mentions neither $better-writing "
            "nor /better-writing",
        )


def check_plugin(expected_name=None, expected_version=None):
    plugin_dir = ROOT / ".claude-plugin"
    manifests = {}
    for filename in ("plugin.json", "marketplace.json"):
        path = plugin_dir / filename
        rel = path.relative_to(ROOT).as_posix()
        try:
            manifests[filename] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{rel}: unreadable ({exc})")
    entries = []
    if "plugin.json" in manifests:
        entries.append((".claude-plugin/plugin.json", manifests["plugin.json"]))
    if "marketplace.json" in manifests:
        plugins = manifests["marketplace.json"].get("plugins") or []
        check(plugins, ".claude-plugin/marketplace.json: no plugins listed")
        entries += [(".claude-plugin/marketplace.json", entry) for entry in plugins]
    for rel, entry in entries:
        if expected_name:
            check(
                entry.get("name") == expected_name,
                f"{rel}: name {entry.get('name')!r} does not match "
                f"SKILL.md name {expected_name!r}",
            )
        if expected_version:
            check(
                entry.get("version") == expected_version,
                f"{rel}: version {entry.get('version')!r} does not match "
                f"SKILL.md metadata.version {expected_version!r}",
            )


def check_layout():
    # The skill used to live at the root. A root SKILL.md makes skills.sh
    # install the whole repo, .claude-plugin/ included, and Claude Code then
    # loads that copy twice: as a skill and as a skills-directory plugin. A
    # root references/ or agents/ is a stale copy nothing ships, such as a
    # file a merge brought back. lexists, so a broken symlink counts too.
    for old in OLD_ROOT_PATHS:
        check(
            not os.path.lexists(ROOT / old),
            f"{old}: must not exist at the repo root; the skill lives in "
            f"{SKILL_DIR.as_posix()}/",
        )
    skills_dir = ROOT / "skills"
    skill = skill_root()
    if not skill.is_dir():
        errors.append(f"{SKILL_DIR.as_posix()}: missing directory")
        return
    # No symlinks: a plain copy, Download ZIP and a Windows checkout would
    # turn them into links that point outside the skill or into path stubs.
    for path in sorted(skills_dir.rglob("*")):
        check(
            not path.is_symlink(),
            f"{path.relative_to(ROOT)}: must be a real file, not a symlink",
        )
    # Root files the skill ships its own copy of, byte for byte.
    for name in SKILL_COPIES:
        copy = skill / name
        rel = copy.relative_to(ROOT).as_posix()
        try:
            same = copy.read_bytes() == (ROOT / name).read_bytes()
        except OSError as exc:
            errors.append(f"{rel}: missing or unreadable ({exc})")
            continue
        check(same, f"{rel}: differs from the root {name}; copy it again")
    # A checkout without symlink support turns a committed symlink into a
    # plain file, which the checks above cannot see, so ask git as well.
    # Skipped when git is unavailable (e.g. source tarball without .git).
    if not (ROOT / ".git").exists():
        return
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-s", "--", "skills"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return
    if proc.returncode != 0:
        return
    for line in proc.stdout.splitlines():
        meta, _, fpath = line.partition("\t")
        if meta.split()[:1] == ["120000"]:
            errors.append(f"{fpath}: tracked as a symlink (git mode 120000); "
                          "commit a real file")


def main():
    skill_name = check_frontmatter()
    check_fixtures()
    check_splits()
    check_triggers()
    version = check_version()
    check_agents(skill_name, version)
    check_plugin(skill_name, version)
    check_layout()
    if errors:
        for message in errors:
            print(f"FAIL {message}")
        print(f"{len(errors)} problem(s) found")
        return 1
    print("all repo checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
