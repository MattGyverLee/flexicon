# Autonomous bug-fix loop -- operating protocol

> **PAUSED 2026-09-21.** The schedule is cancelled; no cron job is armed.
> Do not re-arm it without being asked.
>
> Reason: `fix/348-ocmcodes-none` is parked unfinished (implemented and
> mock-verified, not QC-reviewed, not live-verified) and is **blocked** by
> `SemanticDomainOperations.py:1125`, which raises before the fix is
> reached. Under section 0, the next run would pick that branch up and
> carry on fixing rather than stopping. See
> `specs/348-ocmcodes-none/HANDOFF.md` on that branch, plus #348 and the
> pattern-audit inventory in #352.
>
> To resume: ask for the loop to be restarted. It is an in-memory,
> session-only cron job, so it does not survive a session either way --
> restarting means creating it again, at `23 */3 * * *`, with the prompt
> that points here.

Fired on a schedule. One issue per run. Bug fixes only.

## 0. Bail-out conditions (check first, stop quietly if any hold)

- An earlier loop run left an unfinished branch. Finish that instead of
  picking a new issue. Look for branches matching `fix/<issue>-*` that have
  commits but no open PR.
- No unclaimed issue qualifies (see 1). Stop; do not invent work.

## 1. Pick an issue

`gh issue list --state open --limit 100` (default repo is already
`MattGyverLee/flexicon`; if it ever resolves to `cdfarrow/flexlibs`, run
`gh repo set-default MattGyverLee/flexicon`).

**Bug fixes only.** Skip anything labelled `enhancement`, and skip issues
whose body asks for a new method, kwarg, or capability rather than
correcting existing behaviour. "Add X" is out of scope; "X is broken" is in.

**Exclude anything already being worked on.** An issue is claimed if ANY of:
- a local or remote branch names it (`git branch -a | grep <N>`)
- an open PR references it
- a `specs/*<N>*/` directory exists, tracked or untracked
- it is listed in the `issues` array of any `specs/*/.crew-handoff.json`
  whose `status` is `in_progress`
- it already carries a loop claim comment (see below)

Prefer small, well-shaped, clearly-reproducible bugs over sprawling ones.

Claim it by commenting on the issue before starting work.

## 2. Isolate -- the loop has its own clone

The loop works in **`C:\Github\flexicon-bugfix-loop`**, a **separate full
clone** with its own `.git`. It already exists. Do not recreate it, and do
not delete it when a PR is opened -- it is the loop's permanent home.

**`C:\Github\flexicon` is the user's working repo. Never write to it, and
never run a git command that mutates it** -- no branch, no checkout, no
commit, no worktree, no stash, no fetch. The user works there live;
uncommitted edits have repeatedly been observed appearing mid-run.

Do **not** use `git worktree`. A worktree shares `.git` with the user's
repo, so loop branches, admin dirs and prunes all land in their repo and
confuse it. That is why this is a clone. (It also went wrong on its own: a
worktree removal once left `.git/worktrees/<name>/gitdir` written as NUL
bytes, so the next add silently allocated `<name>1` and produced a
checkout whose tracked files were NUL-filled.)

Reading from the user's repo is fine -- this protocol file lives there,
and the gitignored live fixture is copied from there.

Start each run by syncing the clone and branching from a current `main`:

```
cd C:/Github/flexicon-bugfix-loop
git checkout main && git fetch origin && git reset --hard origin/main
git checkout -b fix/<N>-<slug>
```

Verify the clone is still independent before trusting it -- `.git` must be
a **directory**, not a file (a file means someone turned it into a
worktree):

```
ls -d C:/Github/flexicon-bugfix-loop/.git      # directory
git -C C:/Github/flexicon worktree list        # only the main entry
```

The Target fixture is gitignored, so the clone does not get it from
`git clone` and the live suite fails loudly without it. It persists across
runs; re-copy only if missing:

```
cp "C:/Github/flexicon/tests/fixtures/Target 2026-07-06 0218.fwbackup" \
   C:/Github/flexicon-bugfix-loop/tests/fixtures/
```

`git config core.hooksPath .githooks` is already set in the clone. Check it
survives if the clone is ever rebuilt -- it is local config, not something
a checkout carries.

## 3. Adjudicate before implementing

Dispatch **lex-domain** to rule on any semantic or API question -- what the
correct behaviour is, whether the issue's own proposed fix is right, upstream
`cdfarrow/flexlibs` parity, and what must be confirmed by live probing rather
than source-reading. Ask for a decisive RULING, not a menu of options.

**The issue's suggested fix is a hypothesis, not a spec.** #262 asked for
`Object()` to return `None`; lex-domain rejected that -- it is an
identity-resolution method, and `None` would have converted a loud failure
into a silent no-op on write paths. Follow the ruling, not the issue text.

Run the `sweep-pattern` skill (or dispatch Explore directly) in parallel for
shaped bugs. CLAUDE.md requires a pattern-audit section and lex-qc blocks
approval without one. Fix the chokepoint plus same-class siblings; file
different-class findings as follow-up issues rather than widening the PR.

## 4. Implement

Dispatch **lex-programmer** with the ruling as binding input and an explicit
out-of-scope list. Then **lex-qc** for review.

Never run bare `pytest` or `pytest --ignore=tests/contract` -- both collect
and EXECUTE ~322 `requires_live_project` tests in-place against real FLEx
projects. For mock checks use:
`python -m pytest -m "not requires_live_project" <file> -q`

## 5. Live-verify (REQUIRED for any write-path change)

Per CLAUDE.md this is mandatory and a mock-only pass must never be reported
as verification. Dispatch **lex-verification**.

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest <live test file> -m requires_live_project -q
```

Use the **sandbox** fixtures (`target_sandbox`, `sena3_sandbox`) -- tempdir
copies -- never the in-place `target_project`. Concurrent sessions share the
machine-global projects under `C:\ProgramData\SIL\FieldWorks\Projects`, so
an in-place write can collide with another session's run.

Project choice: **Target** (clean scratch) for write paths, **Sena 3** for
read paths and modify-pre-existing-data. `Ejagham Full` exists on this
machine and is available as an additional read-path corpus when Sena 3
lacks the data, but it has no test fixture and `LIVE_TESTING.md` warns
against substituting Ejagham backups into evidential runs -- do not use it
as a Target substitute.

Evidence is mandatory: `tests/live_status.json` must show
`"run_mode": "live"`, and write
`specs/<N>-<slug>/evidence/live-<task>.md` with the exact command, the
run_mode value, pre-state and post-state **read back from the LCM** (not the
value you passed in), and a pass/fail line.

If live verification is genuinely impossible (locked project, missing
FieldWorks), report `FAIL: unverified`, stop, and leave the branch for a
human. Do not substitute a mock pass.

## 6. Land

- Commit. Do NOT write close/fix/resolve immediately before an issue number
  in prose -- see CLAUDE.md; a `commit-msg` hook enforces this. `closes #N`
  in a footer or subject parenthetical is the genuine convention and passes.
- The hook needs `git config core.hooksPath .githooks`, already set in the
  loop clone. Re-set it if the clone is ever rebuilt.
- Push and PR from the loop clone. Leave the clone in place afterwards;
  just return it to `main` so the next run starts clean.
- Push and open a PR with a **Pattern audit** heading and a link to the live
  evidence file.
- Comment the outcome on the issue. Leave the issue open; the PR closes it.
- Do not merge. Human review is the gate.

## 7. Report

One short line to the user: which issue, what the ruling was, live-verified
or not, and the PR link.
