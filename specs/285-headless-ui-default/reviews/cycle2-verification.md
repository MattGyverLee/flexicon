# Verification Report -- issue #285 POST-FIX conflict measurement

**Verdict:** PASS
**Live run:** yes | **run_mode:** live
**Evidence:** specs/285-headless-ui-default/evidence/live-postfix-conflict.md
**Project:** Target (tempdir sandbox copies only; real Target/Sena 3
untouched, confirmed via `restore_target.py --check`)

## Pinned worktree
`git worktree add <scratch>/post285 4526245`
(`452624520aa7eebf9a4da0d1a53bb403fab63775`, the pure implementation
commit). Confirmed `flexicon/code/FLExLCM.py:99` reads
`ui = HeadlessLcmUI()` at this SHA. Worktree removed on completion
(`git worktree remove --force`; verified via `git worktree list`) so it
cannot re-collide with the concurrent merge into `fix/285-headless-ui-default`.

## Claim vs. observed
| Claim | Observed live | Status |
|-------|---------------|--------|
| Post-fix `ui=None` conflicting save raises `FP_ConflictingSaveError` | Writer2's `SaveChanges()` raised `FP_ConflictingSaveError` with the shipped message text, reproduced under both direct-script and mandated pytest-subprocess invocation | PASS |
| Exception message's claim -- "this session's unsaved changes were NOT discarded" -- holds under re-query | Re-fetched writer2's field via fresh `Object(guid)` in the still-open session: `"writer2_value"` (the in-memory edit, unchanged) -- `RevertToSavedState()` did NOT run | PASS |
| What reaches disk | Fresh third session (opened after both writers closed) read `"writer1_value"` -- the conflict prevented writer2's edit from persisting, but the caller was told via exception, not left to discover it silently | PASS |
| Explicit `ui=FwLcmUI(None, ThreadHelper())` opt-out still reaches the historical path (no `FP_ConflictingSaveError`) | No exception raised in either invocation context; writer2's field silently reverted to `"writer1_value"` (`RevertToSavedState()` ran) -- matches cycle 1's pre-fix measurement of the same code path | PASS |

## Mock suite (regression, supplementary)
Not run in this cycle -- out of scope (post-fix half of a both-sides
live measurement; the offline suite was already run for this branch in
cycle-2-programmer: 1728 passed, 0 failed).

## Blockers
None. The regression check (Goal 3) did not reproduce cycle 1's >105s
block on this run -- it completed in 67.1s under the mandated
pytest-subprocess invocation, showing the silent-discard variant instead.
Per the task's framing, either outcome is accepted as PASS for "reached
the historical path, did not raise `FP_ConflictingSaveError`"; this is
noted, not treated as a discrepancy, and no process was left hung.

## Recommendation
APPROVE. All three required measurements were taken against a real,
pinned-commit LCM, re-querying post-write state rather than asserting on
input values, exactly as both-sides verification requires. The fix
behaves as claimed: a genuine conflicting save now surfaces
`FP_ConflictingSaveError` with the session's pending edit intact, disk
state unchanged from the pre-fix outcome, and the caller informed instead
of silently losing work. The documented opt-out genuinely still reaches
the historical WinForms-`FwLcmUI` path. Both-sides measurement for #285
is now complete (cycle 1 pre-fix + cycle 2 post-fix).
