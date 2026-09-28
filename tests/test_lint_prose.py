"""Rules and exclusions in scripts/lint_prose.py."""

import unittest

import _paths  # noqa: F401
import lint_prose as lp


def lint(text):
    """Run every probe on text the way main() does; return failures."""
    cleaned, raw_map, _ = lp.strip_markdown(text)
    return (lp.check_phrases(cleaned, raw_map, lp.ARTEFACTS, "artefact")
            + lp.check_phrases(cleaned, raw_map, lp.LIVE_SLOP, "live slop")
            + lp.check_contrast(cleaned, raw_map, lp.EMBEDDED_CONTRAST)
            + lp.check_invisible(cleaned, raw_map))


class ProbeTest(unittest.TestCase):
    def test_clean_prose_passes(self):
        self.assertEqual(lint("The dashboard goes live on Monday.\n"), [])

    def test_live_slop_fails_with_raw_line(self):
        failures = lint("Intro.\n\nWe are thrilled to announce it.\n")
        self.assertTrue(failures)
        self.assertTrue(all("raw line 3" in f for f in failures))
        self.assertTrue(any("'thrilled to announce'" in f for f in failures))

    def test_artefact_fails(self):
        failures = lint("Regards,\n[Your Name]\n")
        self.assertTrue(any("artefact '[Your Name]'" in f for f in failures))

    def test_gap_marker_is_not_a_placeholder(self):
        self.assertEqual(lint("Churn rose [churn figure needed].\n"), [])

    def test_contrast_scaffold_fails(self):
        failures = lint("This isn't just an update.\n")
        self.assertTrue(any("isn't just" in f for f in failures))

    def test_word_boundaries_hold(self):
        # "exciting" is banned; a longer word containing it is not.
        self.assertEqual(lint("Unexcitingly, nothing changed.\n"), [])


class ExclusionTest(unittest.TestCase):
    def test_fenced_code_is_skipped(self):
        text = "Before.\n```\nthrilled to announce\n```\nAfter.\n"
        cleaned, raw_map, m = lp.strip_markdown(text)
        self.assertNotIn("thrilled", cleaned)
        self.assertEqual(m["fence_lines"], 3)
        self.assertEqual(raw_map, [1, 5])
        self.assertEqual(lint(text), [])

    def test_blockquote_is_skipped(self):
        text = "> I hope this email finds you well!\nPlain line.\n"
        self.assertEqual(lint(text), [])
        self.assertEqual(lp.strip_markdown(text)[2]["blockquote_lines"], 1)

    def test_inline_code_is_skipped(self):
        self.assertEqual(lint("The checker bans `thrilled`.\n"), [])

    def test_quoted_mention_is_skipped(self):
        self.assertEqual(lint('It flags "thrilled to announce" as a tell.\n'), [])
        self.assertEqual(lint("It flags “moving forward” too.\n"), [])

    def test_unquoted_use_after_quote_still_fails(self):
        self.assertTrue(lint('A "quote" and then moving forward we go.\n'))


class InvisibleCharTest(unittest.TestCase):
    def test_zero_width_space_fails(self):
        self.assertTrue(lp.check_invisible("a​b", [1]))

    def test_stray_joiner_fails(self):
        self.assertTrue(lp.check_invisible("a‍b", [1]))

    def test_joiner_inside_emoji_sequence_passes(self):
        # Regression: the carve-out regex lacked its character class, so
        # every ZWJ sequence (family, profession emoji) was flagged.
        self.assertEqual(lp.check_invisible("\U0001F468‍\U0001F469", [1]), [])
        self.assertEqual(lp.check_invisible("Hi ❤️‍\U0001F525", [1]), [])

    def test_leading_bom_passes(self):
        self.assertEqual(lp.check_invisible("﻿Text", [1]), [])
        self.assertTrue(lp.check_invisible("Te﻿xt", [1]))

    def test_private_use_and_lenticular_fail(self):
        self.assertTrue(lp.check_invisible("xy", [1]))
        self.assertTrue(lp.check_invisible("See 【4†source】.", [1]))


class DashCensusTest(unittest.TestCase):
    def test_ranges_are_exempt(self):
        self.assertEqual(lp.dash_census("Pages 3–5, 2020–2024."), 0)
        self.assertEqual(lp.dash_census("It works — mostly."), 1)


class ContrastSyncTest(unittest.TestCase):
    def test_embedded_copy_matches_checker(self):
        self.assertIsNotNone(lp.CHECKER_CONTRAST)
        self.assertEqual([p for p, _ in lp.CHECKER_CONTRAST],
                         [p for p, _ in lp.EMBEDDED_CONTRAST])


if __name__ == "__main__":
    unittest.main()
