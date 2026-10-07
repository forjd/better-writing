"""The eval runners and release config point at the skill folder validate.py checks."""

import json
import tempfile
import unittest

import _paths  # noqa: F401
import run_skill
import run_triggers
import validate


class SkillPathsTest(unittest.TestCase):
    def test_runners_use_validate_skill_dir(self):
        self.assertEqual(run_skill.SKILL_DIR, validate.ROOT / validate.SKILL_DIR)
        self.assertIs(run_triggers.SKILL_DIR, run_skill.SKILL_DIR)

    def test_prompts_carry_every_reference(self):
        refs = sorted((run_skill.SKILL_DIR / "references").glob("*.md"))
        self.assertTrue(refs)
        prompt = run_skill.build_system_prompt(arm="always-on")
        footer = run_skill.progressive_footer()
        for ref in refs:
            self.assertIn(f"<!-- references/{ref.name} -->", prompt)
            self.assertIn(f"- references/{ref.name}", footer)

    def test_run_metadata_reads_version(self):
        version = run_skill.run_metadata()["skill_version"] or ""
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")

    def test_staging_copies_the_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = run_skill.stage_skill_root(tmp)
            plugin, _ = run_triggers.stage_plugin(tmp)
            for skill in (stage, plugin / "skills" / "better-writing"):
                self.assertTrue((skill / "SKILL.md").is_file())
                self.assertTrue(list((skill / "references").glob("*.md")))

    def test_release_please_files_exist(self):
        config = json.loads((validate.ROOT / "release-please-config.json")
                            .read_text(encoding="utf-8"))
        for entry in config["packages"]["."]["extra-files"]:
            path = entry if isinstance(entry, str) else entry["path"]
            with self.subTest(path=path):
                self.assertTrue((validate.ROOT / path).is_file())


if __name__ == "__main__":
    unittest.main()
