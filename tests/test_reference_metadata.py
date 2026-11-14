"""What a summary records about its commit, and the warnings built on it."""

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
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
    def metadata(self, *results, out_dir=None):
        with mock.patch.object(run_skill, "git", side_effect=list(results)) as git:
            meta = run_skill.run_metadata(out_dir)
        return meta, git

    def test_records_a_dirty_flag(self):
        for stdout, want in ((" M skills/better-writing/SKILL.md\n", True),
                             ("", False)):
            with self.subTest(want=want):
                meta, _ = self.metadata(done(0, "abc1234\n"), done(0, stdout))
                self.assertEqual(meta["commit"], "abc1234")
                self.assertIs(meta["dirty"], want)

    def test_dirty_is_none_when_git_fails(self):
        meta, _ = self.metadata(done(0, "abc1234\n"), done(128))
        self.assertIsNone(meta["dirty"])
        meta, git = self.metadata(done(128))
        self.assertIsNone(meta["commit"])
        self.assertIsNone(meta["dirty"])
        self.assertEqual(git.call_count, 1)

    def test_status_covers_the_inputs_and_skips_outputs(self):
        out_dir = run_skill.ROOT / "evals" / "run-a"
        _, git = self.metadata(done(0, "abc1234\n"), done(), out_dir=out_dir)
        args = git.call_args.args
        self.assertEqual(args[:2], ("status", "--porcelain"))
        for path in ("skills", "evals", ".claude-plugin",
                     ":(exclude)evals/baselines", ":(exclude,literal)evals/run-a"):
            self.assertIn(path, args)

    def test_out_dir_that_holds_inputs_is_not_excluded(self):
        for out in ("evals", "skills", ""):
            with self.subTest(out=out):
                _, git = self.metadata(done(0, "abc1234\n"), done(),
                                       out_dir=run_skill.ROOT / out)
                self.assertEqual(
                    sum(1 for a in git.call_args.args if "exclude" in a), 1)

    def test_out_dir_exclude_is_literal(self):
        _, git = self.metadata(done(0, "abc1234\n"), done(),
                               out_dir=run_skill.ROOT / "evals" / "run[1]")
        self.assertIn(":(exclude,literal)evals/run[1]", git.call_args.args)

    def test_earlier_run_outputs_do_not_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "evals" / "run-b").mkdir(parents=True)
            (root / "evals" / "run-b" / "summary.json").write_text("{}")
            (root / "evals" / "notes").mkdir()
            with mock.patch.object(run_skill, "ROOT", root):
                self.assertTrue(run_skill.is_run_output("?? evals/run-b/"))
                self.assertFalse(run_skill.is_run_output("?? evals/notes/"))
                self.assertFalse(run_skill.is_run_output("?? evals/new.py"))
                self.assertFalse(run_skill.is_run_output(" M evals/run_skill.py"))
                meta, _ = self.metadata(done(0, "abc1234\n"),
                                        done(0, "?? evals/run-b/\n"))
                self.assertIs(meta["dirty"], False)

    def test_main_records_metadata_before_it_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            argv = ["run_skill.py", "--out", str(out), "plain-human"]
            with mock.patch.object(run_skill, "run_metadata",
                                   side_effect=RuntimeError("stop")), \
                    mock.patch("sys.argv", argv):
                with self.assertRaisesRegex(RuntimeError, "stop"):
                    run_skill.main()
            self.assertFalse(out.exists())

    def test_out_dir_outside_the_repo_is_not_excluded(self):
        _, git = self.metadata(done(0, "abc1234\n"), done(),
                               out_dir=run_skill.ROOT.parent / "elsewhere")
        self.assertEqual(sum(1 for a in git.call_args.args if "exclude" in a), 1)


class DefaultBranchTest(unittest.TestCase):
    def test_ancestor_exit_codes(self):
        for code, want in ((0, True), (1, False), (128, None)):
            with self.subTest(code=code), mock.patch.object(
                    run_skill, "git",
                    side_effect=[done(0, "false\n"), done(0, "origin/main\n"),
                                 done(code)]):
                self.assertEqual(run_skill.commit_on_default_branch(),
                                 ("origin/main", want))

    def test_falls_back_to_origin_main(self):
        with mock.patch.object(run_skill, "git",
                               side_effect=[done(0, "false\n"), done(1),
                                            done(0)]) as git:
            self.assertEqual(run_skill.commit_on_default_branch(),
                             ("origin/main", True))
        self.assertEqual(git.call_args.args[-1], "origin/main")

    def test_shallow_clone_cannot_tell(self):
        with mock.patch.object(run_skill, "git",
                               side_effect=[done(0, "true\n")]):
            self.assertEqual(run_skill.commit_on_default_branch(),
                             ("origin/main", None))


class ReferenceWarningsTest(unittest.TestCase):
    def test_clean_commit_on_main_gives_none(self):
        meta = {"commit": "abc1234", "dirty": False}
        self.assertEqual(run_skill.reference_warnings(meta, "origin/main", True), [])

    def test_unknown_state_gives_none(self):
        meta = {"commit": None, "dirty": None}
        self.assertEqual(run_skill.reference_warnings(meta, "origin/main", None), [])

    def test_checkout_that_changed_during_the_run_warns(self):
        meta = {"commit": "abc1234", "dirty": False}
        for end in ({"commit": "def5678", "dirty": False},
                    {"commit": "abc1234", "dirty": True}):
            with self.subTest(end=end):
                warnings = run_skill.reference_warnings(meta, "origin/main",
                                                        True, end)
                self.assertEqual(len(warnings), 1)
                self.assertIn("changed during the run", warnings[0])
        same = run_skill.reference_warnings(meta, "origin/main", True, dict(meta))
        self.assertEqual(same, [])

    def test_ancestry_uses_the_recorded_commit(self):
        with mock.patch.object(run_skill, "git",
                               side_effect=[done(0, "false\n"),
                                            done(0, "origin/main\n"),
                                            done(0)]) as git:
            run_skill.commit_on_default_branch("abc1234")
        self.assertEqual(git.call_args.args[-2], "abc1234")

    def test_dirty_and_off_branch_both_warn(self):
        meta = {"commit": "abc1234", "dirty": True}
        warnings = run_skill.reference_warnings(meta, "origin/main", False)
        self.assertEqual(len(warnings), 2)
        self.assertIn("uncommitted changes", warnings[0])
        self.assertIn("not on origin/main", warnings[1])


class SummaryMetadataTest(unittest.TestCase):
    def test_build_summary_keeps_the_metadata_from_the_start(self):
        meta = {"skill_version": "2.1.0", "commit": "abc1234", "dirty": False,
                "date": "2026-11-14"}
        with mock.patch.object(run_skill, "run_metadata") as later:
            out = run_skill.build_summary("m", "j", False, ["always-on"], 1,
                                          "all", {"f": {"always-on": [True]}},
                                          meta)
        later.assert_not_called()
        for key, value in meta.items():
            self.assertEqual(out[key], value)


class BaselineWarningTest(unittest.TestCase):
    def test_same_settings_give_no_warning(self):
        self.assertNotIn("WARN", diff_output(summary(), summary()))

    def test_skill_version_gap_is_a_note(self):
        out = diff_output(summary(skill_version="2.1.0"),
                          summary(skill_version="2.0.0"))
        self.assertIn("note: baseline is skill 2.0.0, this run is skill 2.1.0", out)
        self.assertNotIn("WARN", out)

    def test_dirty_baseline_warns(self):
        out = diff_output(summary(), summary(dirty=True))
        self.assertIn("uncommitted changes", out)


if __name__ == "__main__":
    unittest.main()
