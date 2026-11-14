# Agent instructions

These rules are for automated agent runs that can share one checkout of this repo with other runs.
The maintainer's orchestrator (Paperclip) starts such runs and sets `PAPERCLIP_WORKSPACE_CWD` and
`PAPERCLIP_AGENT_ID`. Before your first git command, decide which rules apply to you:

- Run `printenv PAPERCLIP_WORKSPACE_CWD`. If it prints a path, this whole file applies.
- If it prints nothing, run `git worktree list`. If it lists worktrees that you did not make, or
  you know that other agents use this checkout, treat the checkout as shared. Rules 1, 3 and 4
  and the last section apply. Instead of the script in Rule 2, make your worktree outside the
  checkout with `git worktree add -b <type>/<task>-<slug> ../<name>`, and remove it with
  `git worktree remove` when you finish. Do the same if the script in Rule 2 exits because a
  variable is missing.
- If you cannot tell, act as in the bullet above.
- None of this file applies only when you know that nobody else uses this checkout at the same
  time: for example, a human in their own clone, or an agent whose user says the clone is theirs
  alone. [CONTRIBUTING.md](./CONTRIBUTING.md) says how to work on the repo.

## Git workspace hygiene for automated agents

This section is for automated agent runs that share a checkout of this repo. The start of this
file says when it applies.

**The shared checkout is the repo itself.** The orchestrator provisions one clone per project,
not one per task, and this project is a single repo — so the clone you are standing in is the
only one every concurrent run has. Running `git checkout` or `git reset` there replaces
another run's working tree mid-task.

This is measured, not theoretical. Concurrent runs on this repo have moved a shared checkout's
HEAD repeatedly inside a single twenty-minute window, including hard resets that discarded
uncommitted changes.

### Rule 1 — never mutate the project checkout

In the project checkout, the only git commands allowed are read-only queries plus `fetch`,
`remote`, and `worktree add|remove|list|prune`.

Never run `checkout`, `switch`, `reset`, `stash`, `merge`, `rebase`, `commit`, `clean`,
`apply`, or `pull` there, and never edit a tracked file there. Every edit happens in your
per-task worktree.

### Rule 2 — work in a per-task worktree

Before your first edit, get an isolated working tree. A linked worktree shares the object
store, so it costs a couple of MB and no extra fetch:

```bash
WT=$(scripts/issue-worktree.sh . FOR-123 docs/123-short-slug)
cd "$WT"
```

The first argument is `.` because this project's checkout is the repo itself; the script also
accepts a subdirectory name for projects that nest several clones under one checkout. The full
signature is `<repo-dir> <issue-key> [branch] [base-ref]`. It prints only the worktree path, is
idempotent across runs on the same task, refuses to steal a branch another worktree already
holds, and never resets an existing branch. Read it before you trust it — it is short.

Then edit, commit, and push entirely from `$WT`. If you are woken again on the same task,
re-run the script; it returns the same path.

### Rule 3 — tear down when the task is finished

Once your branch is pushed and the task is done or handed off:

```bash
git -C "$PAPERCLIP_WORKSPACE_CWD" worktree remove "$WT"
git -C "$PAPERCLIP_WORKSPACE_CWD" worktree prune
```

`$PAPERCLIP_WORKSPACE_CWD` is the project checkout. Use `--force` only when you mean to discard
your own uncommitted changes. Never force-remove a worktree that is not yours — the path
contains the owning agent's id.

### Rule 4 — one branch per task

Git refuses to check out one branch in two worktrees. Name branches after the task
(`<type>/<task-number>-<slug>`) so concurrent tasks cannot collide. If `issue-worktree.sh`
reports the branch is already checked out, another run owns it: coordinate on the task rather
than forcing it.

### If you already edited the project checkout

Stop. Do not commit and do not stash — both make it worse for whoever else is in there. Create
your worktree, re-apply your changes in it, and say what happened on the task.
