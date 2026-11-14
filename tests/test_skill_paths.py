"""The eval runners and release config point at the skill folder validate.py checks."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_every_prompt_carries_the_output_rules(self):
        prompts = [run_skill.build_system_prompt(arm=arm) for arm in run_skill.ARMS]
        prompts.append(run_skill.build_system_prompt(with_skill=False))
        for prompt in prompts:
            self.assertIn(run_skill.OUTPUT_RULES, prompt)

    def test_progressive_header_lists_the_skill_md_description(self):
        text = (run_skill.SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        block = text.split("---\n", 2)[1]
        desc = validate.parse_simple_frontmatter(block)["description"]
        self.assertEqual(run_skill.skill_description(), desc)
        header = run_skill.build_system_prompt(arm="progressive").split("\n\n", 1)[0]
        self.assertIn(f'Installed skill: better-writing — "{desc}"', header)
        manifest = json.loads((validate.ROOT / ".claude-plugin" / "plugin.json")
                              .read_text(encoding="utf-8"))["description"]
        if manifest != desc:
            self.assertNotIn(f'"{manifest}"', header)

    def test_skill_description_reads_frontmatter_only(self):
        manifest = json.loads((validate.ROOT / ".claude-plugin" / "plugin.json")
                              .read_text(encoding="utf-8"))["description"]
        cases = {
            "quoted": ('---\nname: x\ndescription: "Fix prose."\n---\n\nBody.\n',
                       "Fix prose."),
            "crlf": ('---\r\nname: x\r\ndescription: "Fix prose."\r\n'
                     'license: MIT\r\n---\r\n\r\nBody.\r\n', "Fix prose."),
            "folded": ("---\nname: x\ndescription: >\n  Fix prose\n  and keep voice.\n"
                       "license: MIT\n---\n\nBody.\n", "Fix prose and keep voice."),
            "quoted and wrapped": ('---\nname: x\ndescription: "Fix prose\n'
                                   '  and keep voice."\n---\n\nBody.\n',
                                   "Fix prose and keep voice."),
            "wrapped": ("---\nname: x\ndescription: Fix prose\n  and keep voice.\n"
                        "---\n\nBody.\n", "Fix prose and keep voice."),
            "no frontmatter": ("# Title\n\ndescription: not this\n", manifest),
            "body line ignored": ("---\nname: x\n---\n\ndescription: not this\n",
                                  manifest),
        }
        for name, (text, want) in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                Path(tmp, "SKILL.md").write_bytes(text.encode("utf-8"))
                with mock.patch.object(run_skill, "SKILL_DIR", Path(tmp)):
                    self.assertEqual(run_skill.skill_description(), want)

    def test_skill_description_last_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(run_skill, "SKILL_DIR", Path(tmp)), \
                    mock.patch.object(run_skill, "ROOT", Path(tmp)):
                self.assertEqual(run_skill.skill_description(), "better-writing")

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
