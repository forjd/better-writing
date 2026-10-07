"""Error paths in scripts/validate.py, run against temporary repo trees."""

import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import validate

SKILL_DIR = validate.SKILL_DIR.as_posix()
SKILL_PATH = validate.SKILL_MD

SKILL = """---
name: demo-skill
description: A demo skill used by the tests.
metadata:
  version: {version}
---
Body mentions `references/one.md`.
"""


def symlinks_supported():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.symlink("target", Path(tmp) / "link")
        except (OSError, NotImplementedError):
            return False
    return True


class RepoCase(unittest.TestCase):
    """Each test gets an empty repo root and a fresh error list."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        patcher = mock.patch.object(validate, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)
        validate.errors.clear()
        self.addCleanup(validate.errors.clear)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def assertError(self, fragment):
        self.assertTrue(any(fragment in e for e in validate.errors),
                        f"no error containing {fragment!r} in {validate.errors}")


class FrontmatterTest(RepoCase):
    def test_valid(self):
        self.write(SKILL_PATH, SKILL.format(version="1.2.3"))
        self.write(f"{SKILL_DIR}/references/one.md", "x")
        self.assertEqual(validate.check_frontmatter(), "demo-skill")
        self.assertEqual(validate.errors, [])

    def test_missing_reference(self):
        self.write(SKILL_PATH, SKILL.format(version="1.2.3"))
        validate.check_frontmatter()
        self.assertError("mentions references/one.md but it does not exist")

    def test_bad_name(self):
        self.write(SKILL_PATH, SKILL.format(version="1").replace(
            "demo-skill", "Demo_Skill"))
        validate.check_frontmatter()
        self.assertError("must be lowercase")

    def test_folded_description(self):
        data = validate.parse_simple_frontmatter(
            "name: x\ndescription: >\n  one\n  two\nother: 'q'")
        self.assertEqual(data, {"name": "x", "description": "one two", "other": "q"})


class VersionTest(RepoCase):
    def test_matches_manifest(self):
        self.write(SKILL_PATH, SKILL.format(version="1.2.3"))
        self.write(".release-please-manifest.json", '{".": "1.2.3"}')
        self.assertEqual(validate.check_version(), "1.2.3")
        self.assertEqual(validate.errors, [])

    def test_mismatch_with_manifest(self):
        self.write(SKILL_PATH, SKILL.format(version="1.2.3"))
        self.write(".release-please-manifest.json", '{".": "1.2.4"}')
        validate.check_version()
        self.assertError("does not match release manifest '1.2.4'")

    def test_not_semver(self):
        self.write(SKILL_PATH, SKILL.format(version="v1.2"))
        self.write(".release-please-manifest.json", "{}")
        validate.check_version()
        self.assertError("is not MAJOR.MINOR.PATCH")

    def test_agent_version_mismatch(self):
        self.write(f"{SKILL_DIR}/agents/demo.yaml", "name: demo-skill\nversion: 1.0.0\n"
                   "interface:\n  default_prompt: Use $better-writing\n")
        validate.check_agents("demo-skill", "1.2.3")
        self.assertError("version '1.0.0' does not match")


class SplitsTest(RepoCase):
    def setUp(self):
        super().setUp()
        for name in ("a", "b", "c"):
            (self.root / "evals" / "fixtures" / name).mkdir(parents=True)
        # Three fixtures cannot meet the real held-out minimum, so lower it
        # here; test_heldout_minimum checks the floor itself.
        self.addCleanup(setattr, validate, "MIN_HELDOUT", validate.MIN_HELDOUT)
        validate.MIN_HELDOUT = 1

    def splits(self, data):
        self.write("evals/splits.json", json.dumps(data))
        validate.check_splits()

    def test_valid_partition(self):
        self.splits({"dev": ["a", "b"], "heldout": ["c"]})
        self.assertEqual(validate.errors, [])

    def test_overlap(self):
        self.splits({"dev": ["a", "b"], "heldout": ["b", "c"]})
        self.assertError("in both dev and heldout")

    def test_uncovered_fixture(self):
        self.splits({"dev": ["a"], "heldout": ["c"]})
        self.assertError("must cover every fixture exactly once")

    def test_non_string_entries_do_not_crash(self):
        self.splits({"dev": [["a"]], "heldout": ["c"]})
        self.assertError("must hold non-empty strings")

    def test_unknown_key_and_duplicates(self):
        self.splits({"dev": ["a", "a", "b"], "heldout": ["c"], "extra": []})
        self.assertError("lists a fixture twice")
        self.assertError("unknown keys ['extra']")

    def test_heldout_minimum(self):
        validate.MIN_HELDOUT = 2
        self.splits({"dev": ["a", "b"], "heldout": ["c"]})
        self.assertError("heldout has 1 fixtures, needs at least 2")

    def test_invalid_json(self):
        self.write("evals/splits.json", "{")
        validate.check_splits()
        self.assertError("invalid JSON")


class LayoutTest(RepoCase):
    def setUp(self):
        super().setUp()
        self.write(SKILL_PATH, "skill")
        self.write("LICENSE", "licence")
        self.write(f"{SKILL_DIR}/LICENSE", "licence")
        self.skill = self.root / SKILL_DIR

    def test_valid_layout(self):
        validate.check_layout()
        self.assertEqual(validate.errors, [])

    def test_old_root_paths(self):
        self.write("SKILL.md", "skill")
        self.write("references/one.md", "x")
        self.write("agents/demo.yaml", "x")
        validate.check_layout()
        for old in ("SKILL.md", "references", "agents"):
            self.assertError(f"{old}: must not exist at the repo root")

    @unittest.skipUnless(symlinks_supported(), "symlinks unavailable")
    def test_broken_root_symlink(self):
        os.symlink("gone.md", self.root / "SKILL.md")
        validate.check_layout()
        self.assertError("SKILL.md: must not exist at the repo root")

    @unittest.skipUnless(symlinks_supported(), "symlinks unavailable")
    def test_symlinks_anywhere_under_skills(self):
        self.write("notes.md", "x")
        os.remove(self.skill / "SKILL.md")
        os.symlink(os.path.join("..", "..", "notes.md"), self.skill / "SKILL.md")
        (self.root / "skills" / "other").mkdir()
        os.symlink(os.path.join("..", "..", "notes.md"),
                   self.root / "skills" / "other" / "notes.md")
        validate.check_layout()
        hits = [e for e in validate.errors if "must be a real file" in e]
        self.assertEqual(len(hits), 2, validate.errors)

    def test_license_differs(self):
        self.write(f"{SKILL_DIR}/LICENSE", "stale")
        validate.check_layout()
        self.assertError("differs from the root LICENSE")

    def test_license_missing(self):
        os.remove(self.skill / "LICENSE")
        validate.check_layout()
        self.assertError(f"{SKILL_DIR}/LICENSE: missing or unreadable")

    def test_missing_skill_folder(self):
        shutil.rmtree(self.skill)
        validate.check_layout()
        self.assertError(f"{SKILL_DIR}: missing directory")

    @unittest.skipUnless(shutil.which("git"), "git unavailable")
    def test_symlink_in_git_index(self):
        # A checkout without symlink support writes a committed symlink as a
        # plain file, so only the index shows it.
        git = ["git", "-C", str(self.root)]
        subprocess.run(git + ["init", "-q"], check=True)
        blob = subprocess.run(git + ["hash-object", "-w", "LICENSE"],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
        for mode, rel in (("100644", f"{SKILL_DIR}/LICENSE"),
                          ("120000", f"{SKILL_DIR}/README.md")):
            subprocess.run(git + ["update-index", "--add", "--cacheinfo",
                                  f"{mode},{blob},{rel}"], check=True)
        validate.check_layout()
        self.assertEqual(validate.errors, [
            f"{SKILL_DIR}/README.md: tracked as a symlink (git mode 120000); "
            "commit a real file"])


class MainTest(RepoCase):
    def test_main_runs_layout_check(self):
        self.write("SKILL.md", "skill")
        with mock.patch("sys.stdout", new=io.StringIO()):
            self.assertEqual(validate.main(), 1)
        self.assertError("SKILL.md: must not exist at the repo root")


if __name__ == "__main__":
    unittest.main()
