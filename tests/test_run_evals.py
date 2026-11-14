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

    NOT_JUST = "no 'not just X but Y' scaffold"
    ISNT_JUST = "no 'isn't just X' scaffold"
    ITS_NOT = "no 'it's not X, it's Y' scaffold"
    BECAUSE = "no 'not because X but Y' scaffold"

    def structure_hits(self, text):
        return {m.split("structure: ", 1)[1] for m in failed({}, "x", text)
                if m.startswith("structure: ")}

    def test_contrast_scaffolds_fail(self):
        scaffolds = {
            "The tool is not only a linter, but a formatter.": self.NOT_JUST,
            "It's not just fast. But it's cheap.": self.NOT_JUST,
            "It isn't just fast. It's cheap.": self.ISNT_JUST,
            "It isn't just fast… it's cheap.": self.ISNT_JUST,
            "This isn't just a v2.0 refresh, it's a rewrite.": self.ISNT_JUST,
            "This isn't just a tool - it's a partner.": self.ISNT_JUST,
            "The cache isn't just stale, but wrong.": self.ISNT_JUST,
            "It doesn't just save time, it saves money.": self.ISNT_JUST,
            "It doesn't just fix bugs, it prevents them.": self.ISNT_JUST,
            "We don't just build software. We craft experiences.": self.ISNT_JUST,
            "We didn't just build a tool, we built a platform.": self.ISNT_JUST,
            "We didn't just ship it but celebrated it.": self.ISNT_JUST,
            "We didn't just fix it, we fixed the cause.": self.ISNT_JUST,
            "I'm not just a developer, I'm a writer.": self.ISNT_JUST,
            "It's not a bug, it's a feature.": self.ITS_NOT,
            "It's not a bug... it's a feature.": self.ITS_NOT,
            "It's not a config.yml problem, it's a design problem.": self.ITS_NOT,
            "It's not about speed. It's about trust.": self.ITS_NOT,
            "It's not a tool, but a partner.": self.ITS_NOT,
            "We left not because of the pay but because of the hours.": self.BECAUSE,
            "We left not because of the 2.5% cut but because of the hours.":
                self.BECAUSE,
            "The outage was not because of the deploy; it was because of the "
            "logs.": self.BECAUSE,
            "Not because it is easy. Because it is right.": self.BECAUSE,
        }
        for text, desc in scaffolds.items():
            with self.subTest(text=text):
                self.assertIn(desc, self.structure_hits(text))

    def test_ordinary_negations_pass_structure_checks(self):
        sentences = [
            # Issue #71: each of these matched a scaffold before.
            "Do not simply delete the lock file. Stop the worker first.",
            "The fix does not only apply to Postgres.",
            "We did not just restart it: we rolled back the release.",
            "It's not ready yet. We think it's two weeks away.",
            "It is not clear why the export failed. Our guess is that it is "
            "the backup lock.",
            "The outage was not because of the deploy; we found the cause "
            "because of the logs.",
            "It's not ready yet, but it will ship.",
            # Found in review of the fix.
            "Do not just copy the file. Use the script. But check the path first.",
            "Do not simply delete the lock file. Stop the worker first, but "
            "keep the queue.",
            "Don't just stare at it. It starts on its own.",
            "Do not just use the default; you usually need a larger pool.",
            "Don't just be polite, you build trust with facts.",
            "If it's not there, it's in the trash.",
            "When it's not raining, it's sunny.",
            "It is not slow, its cache is warm.",
            "Please don't just copy the file. You will miss the config.",
            "So don't just restart it. It will fail again.",
            "Then do not just retry, it hides the error.",
            "We did not just configure it, we confirmed it worked.",
            "They did not just complete the move, they compared the results.",
            "We did not just record the failure, we recovered the data.",
            "Since it's not cached, it's slow.",
            "Because it's not signed, it's rejected.",
        ]
        for text in sentences:
            with self.subTest(text=text):
                self.assertEqual(self.structure_hits(text), set())

    def test_well_formed_checks_skip_code_and_tables(self):
        texts = [
            "Use `std::vec::Vec` here.",
            "Run `ls ; pwd` first.",
            "| Name  | Value |\n| ----- | ----- |\n| a     | 1     |",
            "Name  | Value\n----- | -----\na     | 1",
            "Run this:\n\n```bash\nls ; pwd\nfoo  bar\n```\n\nDone.",
            "Run this:\n\n~~~\nfoo  bar\n~~~\n\nDone.",
            "| Key | Meaning |\n| --- | --- |\n| ? | optional |\n| ; | separator |",
            "Name  | Value\n-|-\na | 1",
            "Two `Vec`s and `std::fs`s here.",
        ]
        for text in texts:
            with self.subTest(text=text):
                self.assertEqual(failed({}, "x", text), [])

    def test_well_formed_checks_still_fail_prose_damage(self):
        texts = [
            "Our  new release.",
            "Run `ls` , then stop.",
            "Done, ; next.",
            "| Our  new release , | 1 |",
            "I can`t wait ,  and you can`t either.",
            # An unclosed fence does not hide the rest of the text.
            "Wrap it like this:\n```\nRun it  now , please.",
            "```js console.log(1)```\nand  then more ,  text",
        ]
        for text in texts:
            with self.subTest(text=text):
                self.assertTrue(any("well formed" in m for m in failed({}, "x", text)))

    def test_prose_only(self):
        self.assertEqual(re_.prose_only("a\n```\ncode  x\n```\nb"), "a\nb")
        self.assertEqual(re_.prose_only("| a  | b |\n|---|---|\n| c | d |"),
                         "a | b\nc | d")
        self.assertEqual(re_.prose_only("x\n```\ny"), "x\n```\ny")

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
