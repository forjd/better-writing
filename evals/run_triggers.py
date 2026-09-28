#!/usr/bin/env python3
"""Measure whether the skill's description triggers on the right prompts.

Usage:
    python3 evals/run_triggers.py [--model MODEL] [--repeats K] [--out DIR]
    python3 evals/run_triggers.py --jobs 8 tighten-email write-unit-test

run_skill.py always loads the skill, so it cannot see whether a real harness
would load it at all. This runner installs the skill the way a user does, as
a plugin, and sends each prompt in evals/triggers.json through `claude -p`.
The model sees only the harness's skill listing (name plus the SKILL.md
description) next to the built-in skills, and decides for itself whether to
call the Skill tool. A run counts as a trigger when the model invokes
better-writing; the run is stopped at that call, so a triggered prompt never
goes on to do the work.

Two sets, reported separately:

- should_trigger: prose tasks (rewrite, draft, review, copy edit). The
  trigger rate here is recall.
- should_not_trigger: near misses that mention text, emails, or typos but are
  code, data, or translation tasks. The trigger rate here is the false
  trigger rate.

Every run writes <out>/summary.json (default evals/outputs/triggers/) with
per-prompt counts and per-set rates with Wilson 95% intervals. Exits non-zero
if any run errored.
"""

import argparse
import json
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_skill import (DEFAULT_MODEL, ISOLATION_FLAGS, ROOT,  # noqa: E402
                       wilson_interval)

TRIGGERS_PATH = Path(__file__).resolve().parent / "triggers.json"
SETS = ("should_trigger", "should_not_trigger")
SKILL_NAME = "better-writing"
RUN_TIMEOUT = 180
# Read-only tools, so a prompt that does not trigger the skill can still do
# what a real session would (look for files) without writing anything. The
# working directory is an empty staging dir, so there is nothing to find.
TOOLS = "Skill,Read,Glob,Grep"
MAX_BUDGET_USD = "0.50"


def load_triggers(path=TRIGGERS_PATH):
    """Return [(set_name, id, prompt)] from triggers.json."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = []
    for set_name in SETS:
        for case in data[set_name]:
            cases.append((set_name, case["id"], case["prompt"]))
    return cases


def stage_plugin(out_dir):
    """Build a minimal plugin under out_dir/_plugin; return (plugin, cwd).

    The plugin holds the manifest, SKILL.md, and references/ only, the way
    the skills/better-writing tap ships them. Rebuilt on every run, so the
    eval always measures the current working tree's description. The empty
    cwd keeps the model's read-only tools away from the repo.
    """
    plugin = Path(out_dir) / "_plugin"
    shutil.rmtree(plugin, ignore_errors=True)
    skill_dir = plugin / "skills" / SKILL_NAME
    skill_dir.mkdir(parents=True)
    (plugin / ".claude-plugin").mkdir()
    shutil.copy2(ROOT / ".claude-plugin" / "plugin.json",
                 plugin / ".claude-plugin" / "plugin.json")
    shutil.copy2(ROOT / "SKILL.md", skill_dir / "SKILL.md")
    shutil.copytree(ROOT / "references", skill_dir / "references")
    cwd = Path(out_dir) / "_cwd"
    shutil.rmtree(cwd, ignore_errors=True)
    cwd.mkdir(parents=True)
    return plugin, cwd


def skill_calls(event):
    """Return the skill names of every Skill tool_use in a stream-json event."""
    if event.get("type") != "assistant":
        return []
    content = (event.get("message") or {}).get("content") or []
    return [str((block.get("input") or {}).get("skill", ""))
            for block in content
            if block.get("type") == "tool_use" and block.get("name") == "Skill"]


def is_this_skill(name):
    """Match 'better-writing' and the plugin-qualified 'better-writing:better-writing'."""
    return name.split(":")[-1] == SKILL_NAME


def run_one(model, prompt, plugin, cwd, timeout=RUN_TIMEOUT):
    """Run one prompt; return {'triggered': bool, 'skills': [...]}.

    Streams the reply and stops the process once better-writing is called,
    since that call is the whole measurement; a run that calls another
    skill first carries on until it calls this one or finishes. Raises on CLI failure or timeout.
    """
    cmd = ["claude", "-p", prompt, "--model", model, "--tools", TOOLS,
           "--plugin-dir", str(plugin), "--max-budget-usd", MAX_BUDGET_USD,
           "--output-format", "stream-json", "--verbose", *ISOLATION_FLAGS]
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:
        raise OSError(
            "Claude Code CLI (`claude`) not found on PATH. Install it and "
            "authenticate, then retry.") from exc
    timer = threading.Timer(timeout, proc.kill)
    timer.start()
    skills, loaded, finished = [], False, False
    try:
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "system" and event.get("subtype") == "init":
                loaded = any(is_this_skill(s) for s in event.get("skills") or [])
            skills += skill_calls(event)
            if (any(is_this_skill(s) for s in skills)
                    or event.get("type") == "result"):
                finished = True
                break
    finally:
        timed_out = not timer.is_alive()
        timer.cancel()
        if proc.poll() is None:
            proc.kill()
        _, stderr = proc.communicate()
    if timed_out and not finished:
        raise TimeoutError(f"`claude` timed out after {timeout}s")
    if not finished:
        raise RuntimeError(f"`claude` exited {proc.returncode} without a "
                           f"result: {stderr.strip()[:300]}")
    if not loaded:
        raise RuntimeError("the staged plugin did not load: "
                           f"{SKILL_NAME} is missing from the skill listing")
    return {"triggered": any(is_this_skill(s) for s in skills),
            "skills": skills}


def build_summary(model, repeats, results):
    """results: {(set, id): [outcome dict or {'error': str}]}."""
    prompts, sets = [], {}
    for (set_name, case_id), runs in results.items():
        ok = [r for r in runs if "error" not in r]
        hits = sum(r["triggered"] for r in ok)
        other = sorted({s for r in ok for s in r["skills"]
                        if not is_this_skill(s)})
        prompts.append({"set": set_name, "id": case_id, "triggered": hits,
                        "n": len(ok), "errors": [r["error"] for r in runs
                                                 if "error" in r],
                        "other_skills": other})
        agg = sets.setdefault(set_name, {"triggered": 0, "n": 0})
        agg["triggered"] += hits
        agg["n"] += len(ok)
    for agg in sets.values():
        lo, hi = wilson_interval(agg["triggered"], agg["n"])
        agg["rate"] = agg["triggered"] / agg["n"] if agg["n"] else None
        agg["ci95"] = [round(lo, 3), round(hi, 3)]
    return {"model": model, "repeats": repeats, "tools": TOOLS,
            "sets": sets, "prompts": prompts}


def print_summary(summary):
    print(f"model: {summary['model']}  repeats: {summary['repeats']}")
    for p in summary["prompts"]:
        want = "yes" if p["set"] == "should_trigger" else "no"
        extra = f"  other skills: {', '.join(p['other_skills'])}" \
            if p["other_skills"] else ""
        errs = f"  errors: {len(p['errors'])}" if p["errors"] else ""
        print(f"  {p['id']:<28} want {want:<3} triggered "
              f"{p['triggered']}/{p['n']}{extra}{errs}")
    labels = {"should_trigger": "recall (should trigger)",
              "should_not_trigger": "false triggers (should not)"}
    for set_name in SETS:
        agg = summary["sets"].get(set_name)
        if not agg or not agg["n"]:
            continue
        lo, hi = agg["ci95"]
        print(f"{labels[set_name]}: {agg['triggered']}/{agg['n']} = "
              f"{agg['rate']:.2f}  95% CI [{lo:.2f}, {hi:.2f}]")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("ids", nargs="*", help="prompt ids to run (default all)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--jobs", type=int, default=4,
                        help="concurrent `claude` processes (default 4)")
    parser.add_argument("--out", default=str(ROOT / "evals" / "outputs" / "triggers"))
    args = parser.parse_args()
    if args.repeats < 1 or args.jobs < 1:
        parser.error("--repeats and --jobs must be at least 1")

    cases = load_triggers()
    if args.ids:
        known = {c[1] for c in cases}
        unknown = sorted(set(args.ids) - known)
        if unknown:
            parser.error(f"unknown prompt ids: {', '.join(unknown)}")
        cases = [c for c in cases if c[1] in args.ids]

    out = Path(args.out)
    plugin, cwd = stage_plugin(out)
    results = {(s, i): [] for s, i, _ in cases}

    def task(case):
        set_name, case_id, prompt = case
        try:
            outcome = run_one(args.model, prompt, plugin, cwd)
        except (OSError, RuntimeError, TimeoutError) as exc:
            outcome = {"error": str(exc)}
            print(f"  ERROR {case_id}: {exc}", file=sys.stderr)
        return (set_name, case_id), outcome

    jobs = [c for c in cases for _ in range(args.repeats)]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for key, outcome in pool.map(task, jobs):
            results[key].append(outcome)

    summary = build_summary(args.model, args.repeats, results)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                      encoding="utf-8")
    print_summary(summary)
    print(f"summary: {out / 'summary.json'}")
    return 1 if any(p["errors"] for p in summary["prompts"]) else 0


if __name__ == "__main__":
    sys.exit(main())
