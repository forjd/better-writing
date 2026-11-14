"""What a summary records about its commit, and the warnings built on it."""

import contextlib
import io
import subprocess
import unittest
from unittest import mock

import _paths  # noqa: F401
import run_skill


def done(returncode=0, stdout=""):
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")


def summary(**extra):
    base = {"model": "m", "judge_model": "j", "repeats": 5, "split": "all",
            "skill_version": "2.1.0", "commit": "abc1234", "arms": ["always-on"],
            "fixtures": {"f": {"always-on": {"pass": 5, "n": 5, "rate": 1.0}}}}
    base.update(extra)
    return base


def diff_output(new, old):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        run_skill.print_baseline_diff(new, old)
    return out.getvalue()


class RunMetadataTest(unittest.TestCase):
    def test_records_a_dirty_flag(self):
        for stdout, want in ((" M skills/better-writing/SKILL.md\n", True),
                             ("", False)):
            with self.subTest(want=want), \
                    mock.patch.object(run_skill, "git", return_value=done(0, stdout)):
                self.assertIs(run_skill.run_metadata()["dirty"], want)

    def test_dirty_is_none_when_git_fails(self):
        with mock.patch.object(run_skill, "git", return_value=done(128)):
            self.assertIsNone(run_skill.run_metadata()["dirty"])

    def test_status_skips_the_baselines(self):
        with mock.patch.object(run_skill, "git", return_value=done()) as git:
            run_skill.run_metadata()
        args = git.call_args.args
        self.assertEqual(args[:2], ("status", "--porcelain"))
        self.assertIn(":(exclude)evals/baselines", args)


class DefaultBranchTest(unittest.TestCase):
    def test_ancestor_exit_codes(self):
        for code, want in ((0, True), (1, False), (128, None)):
            with self.subTest(code=code), mock.patch.object(
                    run_skill, "git",
                    side_effect=[done(0, "origin/main\n"), done(code)]):
                self.assertEqual(run_skill.commit_on_default_branch(),
                                 ("origin/main", want))

    def test_falls_back_to_origin_main(self):
        with mock.patch.object(run_skill, "git",
                               side_effect=[done(1), done(0)]) as git:
            self.assertEqual(run_skill.commit_on_default_branch(),
                             ("origin/main", True))
        self.assertEqual(git.call_args.args[-1], "origin/main")


class ReferenceWarningsTest(unittest.TestCase):
    def test_clean_commit_on_main_gives_none(self):
        meta = {"commit": "abc1234", "dirty": False}
        self.assertEqual(run_skill.reference_warnings(meta, "origin/main", True), [])

    def test_unknown_state_gives_none(self):
        meta = {"commit": None, "dirty": None}
        self.assertEqual(run_skill.reference_warnings(meta, "origin/main", None), [])

    def test_dirty_and_off_branch_both_warn(self):
        meta = {"commit": "abc1234", "dirty": True}
        warnings = run_skill.reference_warnings(meta, "origin/main", False)
        self.assertEqual(len(warnings), 2)
        self.assertIn("uncommitted changes", warnings[0])
        self.assertIn("not on origin/main", warnings[1])


class BaselineWarningTest(unittest.TestCase):
    def test_same_settings_give_no_warning(self):
        self.assertNotIn("WARN", diff_output(summary(), summary()))

    def test_skill_version_gap_warns(self):
        out = diff_output(summary(skill_version="2.1.0"),
                          summary(skill_version="2.0.0"))
        self.assertIn("WARN skill_version differs", out)

    def test_dirty_baseline_warns(self):
        out = diff_output(summary(), summary(dirty=True))
        self.assertIn("uncommitted changes", out)


if __name__ == "__main__":
    unittest.main()
