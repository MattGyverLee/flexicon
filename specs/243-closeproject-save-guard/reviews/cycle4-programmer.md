# Cycle 4 -- Programmer report: T3 (P0 guard) + T4 (regression proof)

## T3 -- the guard

`flexicon/code/FLExProject.py`, `CloseProject()` (~line 318-380). Two
changes inside the `if not self._undoable:` branch, both in `flexicon/`
only:

1. `if self.HasOpenSessionTask(): ... else: logging.getLogger(__name__).debug(...)`
   -- the `EndNonUndoableTask()` call is now conditional; if no envelope
   is open it is skipped with a debug log rather than assumed present.
2. When the check passes, the `End` call is wrapped in
   `try: self.project.MainCacheAccessor.EndNonUndoableTask() except Exception as e: logging.getLogger(__name__).warning(...)`
   so ANY raise there is swallowed (with the exception type/message
   logged at `[WARN]`) and execution still reaches `usm.Save()` two lines
   later. Lines 326/332 order is unchanged (C7); no reorder attempted.

**Can `HasOpenSessionTask()` raise inside `CloseProject()`?** No. It reads
depth via `_ReadActionHandlerDepth()`, which raises `FP_ProjectError` only
when `not hasattr(self, "project")`. `CloseProject()`'s outer
`if hasattr(self, "project"):` guard (unchanged, line 322) already ensures
`self.project` exists before the new check runs, so the call cannot raise
in this call site. Verified by code inspection, not just assumed.

## T4 -- measured results

Both tests extended in place; **6/6 live, `run_mode: live`**.

- **P-3**: before 0/25 (raise); after **25/25, no raise** -- matches the
  guard's intended fix exactly.
- **P-5**: `SaveChanges()`'s own raise is UNCHANGED (still
  `Commit at wrong place.` at depth 1). `CloseProject()` itself no longer
  raises (guard works as designed). Reopen count: **0/25** -- the "If
  0/25" branch named in advance by the brief, NOT a partial-fix defect.
  The guard reaches `usm.Save()` cleanly, but that `Save()` call persists
  nothing because `SaveChanges()`'s prior `CheckReadyForCommit` failure
  leaves the `UnitOfWorkService` unable to commit later in the same
  session. This is a **NEW FINDING**, recorded as a dated note under
  `spec.md` Q2 (2026-09-07) and it sharpens the existing Q1 follow-up
  already routed to `QUEUE.md` -- a companion `SaveChanges()` guard is
  likely the only path to 25/25 for the owner's real sequence. Not
  absorbed into scope here.

## Q2 disposition

**Left open, with one new dated note added**, not silently resolved:
(a) the original question ("should `CloseProject()`'s whole body get a
`try/finally` so `Dispose()` always runs?") is untouched by T3 -- the
`self.project.Dispose()` path at line ~370 is still reached only via the
pre-existing un-guarded `try/except: raise`. (b) The new P-5 measurement
(0/25, not 25/25) is recorded as a separate dated finding under the same
Q2 heading, since it is adjacent territory (what happens around
`usm.Save()`) but is a distinct question from (a).

## Verification

`run_mode: live` confirmed in `tests/live_status.json`. Marker counts:
probe 6/6 (collect + run), `test_undoable_mode_live.py` 33/33,
`test_target_live_smoke.py` 3/3, `test_transaction_rollback.py` 0 live /
20 offline (all pass). Full offline suite: **1290 passed**, unchanged
before/after. `git diff --stat` touches exactly
`flexicon/code/FLExProject.py`, the probe test file, and `spec.md` -- no
scope-fence files touched.

## Deviations from the frozen contract

None in the guard's design. The only surprise is the P-5 measured
0/25 outcome (a finding, not a contract violation) -- flagged above and
in `spec.md` Q2, not silently adjusted for.

Evidence: `specs/243-closeproject-save-guard/evidence/live-t4-p0-guard-regression.md`
