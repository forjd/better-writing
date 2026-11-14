"""Phrase matching and check logic in evals/run_evals.py."""

import unittest

import _paths  # noqa: F401
import run_evals as re_


def failed(checks, input_text, rewrite):
    return [d for ok, d in re_.check_rewrite(checks, input_text, rewrite) if not ok]


class PhraseFoundTest(unittest.TestCase):
    def test_word_boundaries(self):
        self.assertTrue(re_.phrase_found("37", "about 37 users"))
        self.assertFalse(re_.phrase_found("37", "about 137 users"))
        self.assertFalse(re_.phrase_found("may", "maybe later"))

    def test_flexible_separators(self):
        self.assertTrue(re_.phrase_found("stand-up", "the stand up ran long"))
        self.assertTrue(re_.phrase_found("Reports tab", "open the reports-tab"))

    def test_inflection(self):
        self.assertTrue(re_.phrase_found("sync", "it syncs hourly", inflect=True))
        self.assertFalse(re_.phrase_found("seamless", "seamlessly", inflect=True))
        self.assertTrue(re_.phrase_found("seamless", "seamlessly", inflect="banned"))
        self.assertTrue(re_.phrase_found("underscore", "underscoring it",
                                         inflect="banned"))

    def test_literal_edge_dashes(self):
        self.assertTrue(re_.phrase_found("--dry-run", "pass --dry-run"))
        self.assertFalse(re_.phrase_found("--dry-run", "pass dry-run"))

    def test_curly_apostrophes(self):
        self.assertTrue(re_.phrase_found("isn't just", "It isn’t just that"))

    def test_emoji_uses_substring(self):
        self.assertIsNone(re_.phrase_pattern("🎉"))
        self.assertTrue(re_.phrase_found("🎉", "Launch day🎉"))


class CheckRewriteTest(unittest.TestCase):
    CHECKS = {
        "required": ["15 June"],
        "banned": ["thrilled"],
        "banned_regex": ["—"],
        "max_words_ratio": 1.0,
    }
    INPUT = "We are thrilled to launch on 15 June for everyone here."

    def test_good_rewrite_passes(self):
        self.assertEqual(failed(self.CHECKS, self.INPUT, "It launches on 15 June."), [])

    def test_each_failure_is_reported(self):
        rewrite = ("We are thrilled — truly thrilled — to launch next month "
                   "for absolutely everyone who is here today.")
        messages = failed(self.CHECKS, self.INPUT, rewrite)
        self.assertTrue(any("15 June" in m for m in messages))
        self.assertTrue(any("thrilled" in m for m in messages))
        self.assertTrue(any("/—/" in m for m in messages))
        self.assertTrue(any("length ratio" in m for m in messages))

    def test_contrast_across_lines(self):
        messages = failed({}, "x", "It is not just fast,\nbut cheap.")
        self.assertTrue(any("structure" in m for m in messages))

    def test_contrast_scaffolds_fail(self):
        scaffolds = [
            "It isn't just fast. It's cheap.",
            "The tool is not only a linter, but a formatter.",
            "It doesn't just save time, it saves money.",
            "We didn't just ship it but celebrated it.",
            "It's not a bug, it's a feature.",
            "It's not about speed. It's about trust.",
            "It's not a tool, but a partner.",
            "We left not because of the pay but because of the hours.",
            "The outage was not because of the deploy; it was because of the logs.",
            "Not because it is easy. Because it is right.",
        ]
        for text in scaffolds:
            with self.subTest(text=text):
                self.assertTrue(any("structure" in m for m in failed({}, "x", text)))

    def test_ordinary_negations_pass_structure_checks(self):
        # Issue #71: each of these matched a scaffold before.
        sentences = [
            "Do not simply delete the lock file. Stop the worker first.",
            "The fix does not only apply to Postgres.",
            "We did not just restart it: we rolled back the release.",
            "It's not ready yet. We think it's two weeks away.",
            "It is not clear why the export failed. Our guess is that it is "
            "the backup lock.",
            "The outage was not because of the deploy; we found the cause "
            "because of the logs.",
            "It's not ready yet, but it will ship.",
        ]
        for text in sentences:
            with self.subTest(text=text):
                self.assertEqual(failed({}, "x", text), [])

    def test_well_formed_checks_skip_code_and_tables(self):
        texts = [
            "Use `std::vec::Vec` here.",
            "Run `ls ; pwd` first.",
            "| Name  | Value |\n| ----- | ----- |\n| a     | 1     |",
            "Run this:\n\n```bash\nls ; pwd\nfoo  bar\n```\n\nDone.",
        ]
        for text in texts:
            with self.subTest(text=text):
                self.assertEqual(failed({}, "x", text), [])

    def test_well_formed_checks_still_fail_prose_damage(self):
        texts = [
            "Our  new release.",
            "Run `ls` , then stop.",
            "Done, ; next.",
        ]
        for text in texts:
            with self.subTest(text=text):
                self.assertTrue(any("well formed" in m for m in failed({}, "x", text)))

    def test_malformed_checks_fail_loudly(self):
        messages = failed({"required": "15 June", "banned_regex": ["("]},
                          "x", "y")
        self.assertTrue(any("must be a list" in m for m in messages))
        self.assertTrue(any("invalid" in m for m in messages))

    def test_voice_drift_unknown_marker(self):
        messages = failed({"voice_drift": {"nonsense": 1}}, "a b", "a b")
        self.assertTrue(any("unknown marker" in m for m in messages))

    def test_examples_pass_their_fixtures(self):
        for fixture in sorted(re_.FIXTURES_DIR.iterdir()):
            if not fixture.is_dir():
                continue
            example = fixture.parent.parent / "examples" / f"{fixture.name}.md"
            with self.subTest(fixture=fixture.name):
                checks, input_text = re_.load_fixture(fixture)
                rewrite = example.read_text(encoding="utf-8")
                self.assertEqual(failed(checks, input_text, rewrite), [])


if __name__ == "__main__":
    unittest.main()
