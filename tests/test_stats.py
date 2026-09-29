"""Interval code in evals/run_skill.py against published reference values."""

import unittest

import _paths  # noqa: F401
import run_skill

# Published tables round to 4 dp and use z = 1.959964; the code uses 1.96.
TABLE_TOL = 1e-4


class WilsonIntervalTest(unittest.TestCase):
    # Newcombe RG (1998). Two-sided confidence intervals for the single
    # proportion: comparison of seven methods. Stat Med 17:857-872.
    # Table I, method 3 (Wilson score, no continuity correction).
    CASES = [
        ((81, 263), (0.2553, 0.3662)),
        ((15, 148), (0.0624, 0.1605)),
        ((0, 20), (0.0000, 0.1611)),
        ((1, 29), (0.0061, 0.1718)),
    ]

    def test_newcombe_table(self):
        for (count, n), (lo, hi) in self.CASES:
            with self.subTest(count=count, n=n):
                got_lo, got_hi = run_skill.wilson_interval(count, n)
                self.assertAlmostEqual(got_lo, lo, delta=TABLE_TOL)
                self.assertAlmostEqual(got_hi, hi, delta=TABLE_TOL)

    def test_bounds_clamped(self):
        lo, hi = run_skill.wilson_interval(5, 5)
        self.assertLess(lo, 1.0)
        self.assertEqual(hi, 1.0)

    def test_empty_sample_is_uninformative(self):
        self.assertEqual(run_skill.wilson_interval(0, 0), (0.0, 1.0))


class NewcombeDiffIntervalTest(unittest.TestCase):
    # Newcombe RG (1998). Interval estimation for the difference between
    # independent proportions: comparison of eleven methods. Stat Med
    # 17:873-890. Table II, examples (a)-(h), method 10 (score, no CC).
    CASES = [
        ((56, 70, 48, 80), (0.0524, 0.3339)),
        ((9, 10, 3, 10), (0.1705, 0.8090)),
        ((6, 7, 2, 7), (0.0582, 0.8062)),
        ((5, 56, 0, 29), (-0.0381, 0.1926)),
        ((0, 10, 0, 20), (-0.1611, 0.2775)),
        ((0, 10, 0, 10), (-0.2775, 0.2775)),
        ((10, 10, 0, 20), (0.6791, 1.0000)),
        ((10, 10, 0, 10), (0.6075, 1.0000)),
    ]

    def test_newcombe_table(self):
        for args, (lo, hi) in self.CASES:
            with self.subTest(args=args):
                got_lo, got_hi = run_skill.newcombe_diff_interval(*args)
                self.assertAlmostEqual(got_lo, lo, delta=TABLE_TOL)
                self.assertAlmostEqual(got_hi, hi, delta=TABLE_TOL)

    def test_antisymmetric(self):
        lo, hi = run_skill.newcombe_diff_interval(4, 5, 5, 5)
        rlo, rhi = run_skill.newcombe_diff_interval(5, 5, 4, 5)
        self.assertAlmostEqual(lo, -rhi)
        self.assertAlmostEqual(hi, -rlo)

    def test_readme_example(self):
        # evals/README.md: K=5, progressive 4/5 vs always-on 5/5.
        lo, hi = run_skill.newcombe_diff_interval(4, 5, 5, 5)
        self.assertAlmostEqual(lo, -0.62, places=2)
        self.assertAlmostEqual(hi, 0.26, places=2)

    def test_empty_arm(self):
        self.assertEqual(run_skill.newcombe_diff_interval(0, 0, 1, 2), (0.0, 0.0))


class PairedMeanDiffIntervalTest(unittest.TestCase):
    def test_worked_example(self):
        # diffs 1..5: mean 3, sd sqrt(2.5), t(0.975, 4) = 2.776.
        mean, lo, hi = run_skill.paired_mean_diff_interval([1, 2, 3, 4, 5])
        half = 2.776 * (2.5 ** 0.5) / (5 ** 0.5)
        self.assertEqual(mean, 3)
        self.assertAlmostEqual(lo, 3 - half)
        self.assertAlmostEqual(hi, 3 + half)

    def test_t_table_spot_values(self):
        # Standard two-sided 95% t critical values.
        for df, t in {1: 12.706, 4: 2.776, 12: 2.179, 30: 2.042}.items():
            with self.subTest(df=df):
                self.assertEqual(run_skill._T95[df], t)
        self.assertEqual(sorted(run_skill._T95), list(range(1, 31)))

    def test_large_sample_falls_back_to_normal(self):
        diffs = [0, 1] * 20  # 40 values, df 39
        mean, lo, hi = run_skill.paired_mean_diff_interval(diffs)
        import statistics
        half = 1.96 * statistics.stdev(diffs) / (40 ** 0.5)
        self.assertAlmostEqual(hi - mean, half)

    def test_degenerate_inputs(self):
        self.assertEqual(run_skill.paired_mean_diff_interval([]), (0.0, 0.0, 0.0))
        self.assertEqual(run_skill.paired_mean_diff_interval([0.4]), (0.4, 0.4, 0.4))
        self.assertEqual(run_skill.paired_mean_diff_interval([0.2, 0.2]),
                         (0.2, 0.2, 0.2))


class ReplyParsingTest(unittest.TestCase):
    def test_last_array_wins(self):
        reply = '["a claim"]\nWait, that is in the source. Correcting: []'
        self.assertEqual(run_skill.parse_claims(reply), [])

    def test_fenced_array(self):
        reply = '```json\n["one", " two "]\n```'
        self.assertEqual(run_skill.parse_claims(reply), ["one", "two"])

    def test_no_array_is_none(self):
        self.assertIsNone(run_skill.parse_claims("No added claims."))

    def test_strip_preamble_keeps_real_opener(self):
        text = "Here is what changed in the second quarter.\nMore.\n"
        self.assertEqual(run_skill.strip_preamble(text), text)

    def test_strip_preamble_drops_label_and_fence(self):
        text = "Here's the rewrite:\n```markdown\nBody text.\n```"
        self.assertEqual(run_skill.strip_preamble(text), "Body text.\n")


if __name__ == "__main__":
    unittest.main()
