---
name: speckit-round
description: Run exactly ONE round of the post-clarify Companion pipeline in this (fresh) session -- the plan step, the tasks step, or one implement phase -- then stop at a boundary the disk records. Driven by scripts/speckit_rounds.py or scripts/speckit_rounds_opencode.py, one new session per round; also usable by hand in a fresh chat.
compatibility: Requires spec-kit project structure with .specify/ and the companion extension
---

## User Input

```text
$ARGUMENTS
```

A feature directory (`specs/NNN-name`). If absent, use `.specify/feature.json`.

## What a round is

The pipeline after clarify is split into rounds, each run by a **fresh
top-level session** so it starts near-empty and can dispatch its own
subagents:

| Round | Work |
|-------|------|
| plan | `speckit-companion-plan`, fully |
| tasks | `speckit-companion-tasks`, fully |
| implement | ONE phase of `tasks.md` -- the phase containing the next unchecked task |

All memory between rounds is on disk: `.spec-context.json` (step, status,
decisions) and the checkboxes in `tasks.md`. Nothing is carried in chat.
That is what makes a new session per round cheap: orientation is one status
call plus the artifacts this round actually needs.

## Steps

1. **Resolve.**

   ```bash
   python3 .specify/extensions/companion/scripts/status-context.py --feature-dir <feature_dir>
   ```

   Parse the final `RESOLUTION: {...}` line. If `complete: true`, end with
   `ROUND: COMPLETE`. If `empty: true` or the next step is specify/clarify,
   end with `ROUND: BLOCKED needs interactive specify/clarify`.

2. **Unattended.** This round has no human watching:

   ```bash
   python3 .specify/extensions/companion/scripts/write-context.py --feature-dir <feature_dir> --set unattended=true
   ```

   Review gates are recorded and passed, never waited on. State the
   RESOLUTION `decisions[]` as in-scope context for the step.

3. **Do the round's work by invoking the real command -- never re-enact it.**

   - **plan** -> invoke `speckit-companion-plan <feature_dir>` and let it run
     to its `--advance`. Dispatch its per-area investigation workers as the
     skill directs.
   - **tasks** -> invoke `speckit-companion-tasks <feature_dir>` and let it
     run to its `--advance`.
   - **implement** -> invoke `speckit-companion-implement <feature_dir>` with
     this scope limit: **this round owns only the phase containing
     `nextTask`** (the `## Phase` / `## Checkpoint` heading above it in
     `tasks.md`). Within that phase follow the skill exactly: wave order,
     join checks, worker dispatch, `--close-task` or `--append` +
     `--materialize` for every task. Specify/plan/tasks did **not** run in
     this session, so the reading is not spent: dispatch per the skill's
     threshold. Once the phase's last task is folded, checkpoint it (step 4) and stop.
     Run implement's wrap-up (full suite via one worker, the capture
     `--batch`, living-spec accounting, `--mark-complete`) **only** if no
     unchecked task remains anywhere in `tasks.md` after this phase.

4. **Checkpoint the phase (implement rounds only).** Once the phase's last
   task is folded, commit and push the phase's code on the feature branch,
   so every phase is a rollback point other agents can see. Running the
   rounds driver is the developer's standing request for these commits.

   - **Where:** the checkout that holds the feature branch -- the worktree
     from `git worktree list` whose branch is the feature branch (for
     example `C:/Github/flexicon-572` on `fix/572-phonological-rule-readers`).
     The driver starts the session there, so relative paths already land in
     the worktree; when you dispatch workers, tell them that checkout's
     absolute path. Never commit anything on `main`; if no feature branch
     exists, end `ROUND: BLOCKED no feature branch to commit phase code to`.
   - **Test first, when there is something to test.** Run the offline tests
     the phase added or touched:
     `python -m pytest -m "not requires_live_project" -q <test files>`.
     Run the full offline gate (`python -m pytest -m "not requires_live_project" -q`)
     instead when the phase touched shared code (`BaseOperations`,
     `FLExProject`, `Shared/`, sync) or is the last phase. Run every live
     test file the phase added or touched with `FLEXLIBS_REQUIRE_LIVE=1`
     (`python -m pytest <file> -m requires_live_project -q`) and check
     `tests/live_status.json` says `"run_mode": "live"`. Never bare `pytest`.
     A phase that changed only docs needs no test run. A `### Tests` block
     the plan says must fail first is red **only within its phase**; by the
     checkpoint the phase's own tests must pass.
   - **Red tests, or live evidence missing: no commit, no push.** End
     `ROUND: BLOCKED phase tests red: <failing tests>` or
     `ROUND: BLOCKED FAIL: unverified <why>`.
   - **Green:** make sure the commit-msg hook is on
     (`git -C <worktree> config core.hooksPath .githooks`), then stage
     everything (the spec folder included), commit, push with an explicit
     refspec:

     ```bash
     git -C <worktree> add -A -- .
     git -C <worktree> commit -m "feat(<feature>): <phase title> (T###-T###)" -m "<one line per task: id + what it did>"
     git -C <worktree> push -u origin HEAD:refs/heads/<branch>
     ```

     End the message with your harness's commit attribution line if it
     defines one. **No close keyword** (`close`, `fix`, `resolve` and their
     forms) directly before an issue number in a phase commit: the issue
     closes when the PR merges, not per phase (CLAUDE.md, Commits). If the
     hook rejects the message, reword it; never `--no-verify`. Always use
     the explicit `HEAD:refs/heads/<branch>` refspec: a worktree created
     from main may track `origin/main`, and a bare `git push` would then
     push onto main. Never force-push. If the push is rejected, end
     `ROUND: BLOCKED push rejected: <reason>`.
   - **The spec folder rides with the branch.** `specs/<feature>/` lives on
     the feature branch next to the code and reaches main only when the PR
     merges. The driver also commits and pushes it on the branch after every
     round (`scripts/speckit_git.py`); round logs (`specs/<feature>/rounds/`)
     stay local through the folder's `.gitignore`. Running a round by hand
     without a driver? Finish with `python scripts/speckit_git.py sync <feature_dir>`.

   Put the commit sha in your `ROUND: DONE` line.

5. **Honour the project's CLAUDE.md.** It binds this session and every
   worker you dispatch. In flexicon: any change touching an Operations
   class, factory call, setter, `FLExProject` or the write path needs the
   live LCM verification and evidence file; if it cannot be done, the task
   is not done -- end with `ROUND: BLOCKED FAIL: unverified <why>`.

6. **Stop.** Do not start the next step or the next phase, even if context
   remains. The driver starts a fresh session for it.

## Final line (the driver parses it)

End your last message with exactly one of:

```text
ROUND: DONE <one-line summary: step or phase, files touched, tests, commit sha>
ROUND: COMPLETE
ROUND: BLOCKED <reason>
```

`BLOCKED` is for things a new session cannot fix by trying again: a scope
question for the developer, unverifiable live work, a repeated worker
failure, a broken environment.
