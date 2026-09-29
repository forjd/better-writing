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
