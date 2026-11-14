"""compare_outputs.py's verdict parser, run_triggers.py, and run_skill.py's
split loader, judge-only mode and summary builders (issue #80)."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import compare_outputs
import run_skill
import run_triggers


def capture(func, *args, **kwargs):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = func(*args, **kwargs)
    return result, out.getvalue()


class ParseVerdictTest(unittest.TestCase):
    def check(self, cases):
        for reply, want in cases.items():
            with self.subTest(reply=reply):
                self.assertEqual(compare_outputs.parse_verdict(reply), want)

    def test_verdict_alone_on_the_final_line_wins(self):
        self.check({
            "2": "2",
            "**1**": "1",
            "1.": "1",
            "Rewrite 1 pads and Rewrite 2 is plain.\n2": "2",
            "Rewrite 1 pads and Rewrite 2 is plain.\n2\n\n": "2",
            "Rewrite 1 adds a date.\nRewrite 2 keeps every fact.\nRewrite 2.": "2",
            "Rewrite 1 adds a date.\n\n**Rewrite 2**": "2",
            "Rewrite 1 pads.\nAnswer: 2": "2",
            "Rewrite 1 pads and adds a date.\nVerdict: **2**": "2",
        })

    def test_prose_is_no_verdict(self):
        self.check({
            # Issue #80: the loser named second used to be read as the winner.
            "Rewrite 2 is better because Rewrite 1 pads.": None,
            "Rewrite 1 invents a claim, so 2.": None,
            # A lone mention may be the loser.
            "Rewrite 1 pads.": None,
            "Loser: Rewrite 1": None,
            "Rewrite 2 is better.\nRewrite 1 pads.": None,
            "The second one (2) reads better": None,
            "1 pads, 2 does not, overall": None,
        })

    def test_nothing_to_read(self):
        self.check({"Version 1.2 is fine": None, "": None, "  \n ": None})


class AskTest(unittest.TestCase):
    def run_ask(self, *replies):
        results = [subprocess.CompletedProcess([], 0, stdout=r, stderr="")
                   for r in replies]
        with mock.patch.object(compare_outputs.subprocess, "run",
                               side_effect=results) as run:
            verdict, _ = capture(compare_outputs.ask, "m", "prompt", retries=2)
        return verdict, run.call_count

    def test_unclear_reply_is_asked_again(self):
        self.assertEqual(
            self.run_ask("Rewrite 2 is better because Rewrite 1 pads.", "2"),
            ("2", 2))

    def test_unclear_every_time_is_none(self):
        self.assertEqual(self.run_ask("Rewrite 1, Rewrite 2", "1 or 2", "both"),
                         (None, 3))


class CompareMainTest(unittest.TestCase):
    def test_unclear_verdict_counts_as_a_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            dir_a, dir_b = Path(tmp, "a"), Path(tmp, "b")
            for folder in (dir_a, dir_b):
                folder.mkdir()
                for name in ("plain-human", "launch-email"):
                    (folder / f"{name}.md").write_text("Text.\n", encoding="utf-8")
            verdicts = iter(["1", "2", None, "2"])
            argv = ["compare_outputs.py", str(dir_a), str(dir_b),
                    "launch-email", "plain-human"]
            with mock.patch.object(compare_outputs, "ask",
                                   side_effect=lambda *a: next(verdicts)), \
                    mock.patch.object(sys, "argv", argv):
                code, text = capture(compare_outputs.main)
        self.assertEqual(code, 0)
        self.assertIn("launch-email: A (orders: 1, 2)", text)
        self.assertIn("plain-human: skipped (orders: ?, 2)", text)
        self.assertIn("A wins 1, B wins 0, ties 0, skips 1", text)


class SkillCallsTest(unittest.TestCase):
    def test_reads_skill_tool_uses_from_assistant_events(self):
        event = {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "hi"},
            {"type": "tool_use", "name": "Skill", "input": {"skill": "better-writing"}},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "x"}},
            {"type": "tool_use", "name": "Skill", "input": {"skill": "other"}},
        ]}}
        self.assertEqual(run_triggers.skill_calls(event), ["better-writing", "other"])

    def test_ignores_other_events_and_missing_fields(self):
        self.assertEqual(run_triggers.skill_calls({"type": "user"}), [])
        self.assertEqual(run_triggers.skill_calls({"type": "assistant"}), [])
        # A Skill call with no name says nothing, so it is dropped.
        for block in ({"type": "tool_use", "name": "Skill"},
                      {"type": "tool_use", "name": "Skill", "input": {"skill": None}}):
            self.assertEqual(run_triggers.skill_calls(
                {"type": "assistant", "message": {"content": [block]}}), [])

    def test_is_this_skill(self):
        self.assertTrue(run_triggers.is_this_skill("better-writing"))
        self.assertTrue(run_triggers.is_this_skill("better-writing:better-writing"))
        self.assertFalse(run_triggers.is_this_skill("better-writing-extra"))
        self.assertFalse(run_triggers.is_this_skill("other:skill"))
        # Any plugin's copy of the skill counts: the name after the colon is
        # the skill, and the eval stages only this repo's plugin.
        self.assertTrue(run_triggers.is_this_skill("other-plugin:better-writing"))


class TriggerSummaryTest(unittest.TestCase):
    RESULTS = {
        ("should_trigger", "email"): [
            {"triggered": True, "skills": ["better-writing"]},
            {"triggered": False, "skills": ["other"]},
            {"error": "TimeoutError: slow"},
        ],
        ("should_not_trigger", "code"): [
            {"triggered": False, "skills": []},
            {"triggered": False, "skills": []},
        ],
    }

    def test_counts_rates_and_errors(self):
        summary = run_triggers.build_summary("m", 3, self.RESULTS)
        prompts = {p["id"]: p for p in summary["prompts"]}
        self.assertEqual(prompts["email"]["triggered"], 1)
        self.assertEqual(prompts["email"]["n"], 2)
        self.assertEqual(prompts["email"]["errors"], ["TimeoutError: slow"])
        self.assertEqual(prompts["email"]["other_skills"], ["other"])
        self.assertEqual(summary["sets"]["should_trigger"]["rate"], 0.5)
        self.assertEqual(summary["sets"]["should_not_trigger"]["rate"], 0.0)
        lo, hi = summary["sets"]["should_not_trigger"]["ci95"]
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.0)

    def test_all_errors_gives_no_rate(self):
        summary = run_triggers.build_summary(
            "m", 1, {("should_trigger", "x"): [{"error": "boom"}]})
        self.assertIsNone(summary["sets"]["should_trigger"]["rate"])


class RunCaseTest(unittest.TestCase):
    def test_any_exception_becomes_an_error_outcome(self):
        def broken(*args):
            raise ValueError("bad stream")
        with contextlib.redirect_stderr(io.StringIO()):
            key, outcome = run_triggers.run_case(
                "m", ("should_trigger", "x", "prompt"), "plugin", "cwd", broken)
        self.assertEqual(key, ("should_trigger", "x"))
        self.assertEqual(outcome, {"error": "ValueError: bad stream"})

    def test_success_passes_the_outcome_through(self):
        def ok(model, prompt, plugin, cwd):
            return {"triggered": True, "skills": [prompt]}
        _, outcome = run_triggers.run_case("m", ("s", "x", "p"), "pl", "cwd", ok)
        self.assertEqual(outcome, {"triggered": True, "skills": ["p"]})


class TriggersMainTest(unittest.TestCase):
    def test_one_failed_run_keeps_the_others(self):
        cases = [("should_trigger", "good", "Rewrite this."),
                 ("should_not_trigger", "bad", "Explain this.")]

        def fake_run_one(model, prompt, plugin, cwd):
            if prompt == "Explain this.":
                raise ValueError("bad stream")
            return {"triggered": True, "skills": ["better-writing"]}
        with tempfile.TemporaryDirectory() as tmp:
            argv = ["run_triggers.py", "--out", tmp, "--repeats", "2", "--jobs", "2"]
            with mock.patch.object(run_triggers, "load_triggers", return_value=cases), \
                    mock.patch.object(run_triggers, "run_one", fake_run_one), \
                    mock.patch.object(sys, "argv", argv), \
                    contextlib.redirect_stderr(io.StringIO()):
                code, _ = capture(run_triggers.main)
            summary = json.loads(Path(tmp, "summary.json").read_text())
        self.assertEqual(code, 1)
        prompts = {p["id"]: p for p in summary["prompts"]}
        self.assertEqual((prompts["good"]["triggered"], prompts["good"]["n"]), (2, 2))
        self.assertEqual(prompts["bad"]["errors"], ["ValueError: bad stream"] * 2)


class FakeProcess:
    """Enough of subprocess.Popen for run_one: stdout lines and an exit."""

    def __init__(self, events, returncode=0):
        self.stdout = iter([json.dumps(e) + "\n" if isinstance(e, dict) else e
                            for e in events])
        self.returncode = returncode

    def poll(self):
        return self.returncode

    def kill(self):
        pass

    def communicate(self):
        return "", "stderr text"


class RunOneTest(unittest.TestCase):
    INIT = {"type": "system", "subtype": "init", "skills": ["better-writing:better-writing"]}
    CALL = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Skill", "input": {"skill": "better-writing"}}]}}
    RESULT = {"type": "result"}

    def run_one(self, events):
        with mock.patch.object(run_triggers.subprocess, "Popen",
                               return_value=FakeProcess(events)):
            return run_triggers.run_one("m", "prompt", "plugin", "cwd", timeout=30)

    def test_triggered_stops_at_the_call(self):
        outcome = self.run_one([self.INIT, "not json\n", self.CALL,
                                {"type": "assistant", "message": {"content": [
                                    {"type": "tool_use", "name": "Skill",
                                     "input": {"skill": "other"}}]}}])
        self.assertEqual(outcome, {"triggered": True, "skills": ["better-writing"]})

    def test_not_triggered_ends_at_the_result(self):
        self.assertEqual(self.run_one([self.INIT, self.RESULT]),
                         {"triggered": False, "skills": []})

    def test_no_result_raises(self):
        with self.assertRaisesRegex(RuntimeError, "without a result"):
            self.run_one([self.INIT])

    def test_plugin_not_loaded_raises(self):
        init = dict(self.INIT, skills=["other"])
        with self.assertRaisesRegex(RuntimeError, "did not load"):
            self.run_one([init, self.RESULT])


class LoadSplitTest(unittest.TestCase):
    def test_known_splits(self):
        self.assertIsNone(run_skill.load_split("all"))
        dev, heldout = run_skill.load_split("dev"), run_skill.load_split("heldout")
        self.assertTrue(dev and heldout)
        self.assertFalse(set(dev) & set(heldout))

    def test_bad_splits_raise(self):
        cases = {
            "unknown": ('{"dev": ["a"]}', "nope", "unknown split"),
            "not json": ("{", "dev", "cannot parse"),
            "top level not an object": ('["dev"]', "dev", "unknown split"),
            "not a list": ('{"dev": "a"}', "dev", "must be a list"),
            "empty name": ('{"dev": [""]}', "dev", "must be a list"),
            "not a string": ('{"dev": [1]}', "dev", "must be a list"),
        }
        for name, (text, split, message) in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp, "splits.json")
                path.write_text(text, encoding="utf-8")
                with mock.patch.object(run_skill, "SPLITS_PATH", path):
                    with self.assertRaisesRegex(ValueError, message):
                        run_skill.load_split(split)

    def test_missing_file_raises(self):
        with mock.patch.object(run_skill, "SPLITS_PATH", Path("/nonexistent/splits.json")):
            with self.assertRaisesRegex(ValueError, "cannot read"):
                run_skill.load_split("dev")


class JudgeOnlyTest(unittest.TestCase):
    def fixtures(self, *names):
        return [run_skill.FIXTURES_DIR / name for name in names]

    def test_writes_claims_and_reports_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "plain-human.md").write_text("Plain text.\n", encoding="utf-8")
            (out / "launch-email.md").write_text("Launch text.\n", encoding="utf-8")
            expected = {}
            for name in ("plain-human", "launch-email"):
                checks, source = run_skill.load_fixture(run_skill.FIXTURES_DIR / name)
                expected[source] = (checks["brief"], name)
            claims = {"plain-human": [], "launch-email": ["an invented date"]}

            def judge(model, brief, source, rewrite):
                want_brief, name = expected[source]
                self.assertEqual(brief, want_brief)
                self.assertEqual(rewrite, (out / f"{name}.md").read_text())
                return claims[name]
            with mock.patch.object(run_skill, "judge_added_claims", judge):
                code, text = capture(run_skill.judge_only, "j", out,
                                     self.fixtures("launch-email", "plain-human"))
            self.assertEqual(code, 1)
            self.assertIn("added claim: an invented date", text)
            self.assertEqual(json.loads((out / "plain-human.claims.json").read_text()), [])
            self.assertEqual(json.loads((out / "launch-email.claims.json").read_text()),
                             ["an invented date"])

    def test_review_fixture_skips_the_judge(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "review-findings.md").write_text("F1.\n", encoding="utf-8")
            (out / "review-findings.claims.json").write_text("[]\n")
            with mock.patch.object(run_skill, "judge_added_claims") as judge:
                code, text = capture(run_skill.judge_only, "j", out,
                                     self.fixtures("review-findings"))
            judge.assert_not_called()
            self.assertEqual(code, 0)
            self.assertFalse((out / "review-findings.claims.json").exists())

    def test_judge_error_and_no_rewrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            code, _ = capture(run_skill.judge_only, "j", out,
                              self.fixtures("plain-human"))
            self.assertEqual(code, 2)
            (out / "plain-human.md").write_text("Text.\n", encoding="utf-8")
            (out / "plain-human.claims.json").write_text("[]\n")
            with mock.patch.object(run_skill, "judge_added_claims",
                                   side_effect=run_skill.JudgeError("bad reply")):
                code, text = capture(run_skill.judge_only, "j", out,
                                     self.fixtures("plain-human"))
            self.assertEqual(code, 1)
            self.assertIn("FAIL judge error", text)
            # A stale result must not read as "judged, no added claims".
            self.assertFalse((out / "plain-human.claims.json").exists())


META = {"skill_version": "0.0.0", "commit": None, "dirty": None, "date": "2026-11-14"}


class SummaryBuilderTest(unittest.TestCase):
    RESULTS = {
        "a": {"always-on": [True] * 5, "progressive": [True, True, False, False, False]},
        "b": {"always-on": [True, False, True, False, True], "progressive": [True] * 5},
    }

    def test_per_fixture_entries(self):
        summary = run_skill.build_summary("m", "j", False, run_skill.ARMS, 5,
                                          "dev", self.RESULTS, META)
        a = summary["fixtures"]["a"]
        self.assertEqual((a["always-on"]["pass"], a["always-on"]["n"]), (5, 5))
        self.assertEqual(a["progressive"]["rate"], 0.4)
        self.assertEqual(a["always-on"]["ci95"],
                         list(run_skill.wilson_interval(5, 5)))
        self.assertAlmostEqual(a["diff_progressive_minus_always_on"], -0.6)
        self.assertEqual(a["diff_ci95"],
                         list(run_skill.newcombe_diff_interval(2, 5, 5, 5)))
        self.assertEqual(summary["overall"]["always-on"]["pass"], 8)
        self.assertEqual(summary["overall"]["n_fixtures"], 2)
        self.assertAlmostEqual(summary["overall"]["paired_mean_diff"], -0.1)
        self.assertEqual((summary["judge_model"], summary["split"]), ("j", "dev"))

    def test_no_judge_records_none(self):
        summary = run_skill.build_summary("m", "j", True, ["always-on"], 1,
                                          "all", {"a": {"always-on": [True]}}, META)
        self.assertIsNone(summary["judge_model"])
        self.assertIs(summary["no_judge"], True)

    def test_one_arm_has_no_paired_difference(self):
        summary = run_skill.build_summary("m", "j", False, ["always-on"], 1,
                                          "all", {"a": {"always-on": [True]}}, META)
        self.assertNotIn("paired_mean_diff", summary["overall"])

    def test_baseline_diff_per_fixture_lines(self):
        def summary(fixtures, **extra):
            return {"arms": ["always-on"], "model": "m", "fixtures": {
                name: {"always-on": {"pass": c, "n": 5, "rate": c / 5}}
                for name, c in fixtures.items()}, **extra}
        _, text = capture(run_skill.print_baseline_diff,
                          summary({"a": 5, "new": 3}), summary({"a": 2, "old": 4}))
        lo, hi = run_skill.newcombe_diff_interval(5, 5, 2, 5)
        self.assertIn(f"  a: 2/5 -> 5/5, diff +0.60 [{lo:+.2f}, {hi:+.2f}]", text)
        self.assertIn("  new: only in this run", text)
        self.assertIn("  old: only in baseline", text)
        self.assertIn("2/5 -> 5/5", text.splitlines()[-1])

    def test_baseline_with_no_shared_arm(self):
        new = {"arms": ["progressive"], "fixtures": {}}
        old = {"arms": ["always-on"], "fixtures": {}}
        _, text = capture(run_skill.print_baseline_diff, new, old)
        self.assertIn("no arm in common (baseline: always-on)", text)


if __name__ == "__main__":
    unittest.main()
