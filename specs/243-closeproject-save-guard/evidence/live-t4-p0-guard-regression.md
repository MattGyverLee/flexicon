# Evidence -- T4 P0 guard regression (issue #243, CP-B / T3-T4)

Date: 2026-09-07 (spurt 4, cycle 4)
Fixture: `target_sandbox_path` / `target_sandbox` ONLY. The real Target
project was never opened; no `scripts/restore_*.py` was run.

## Commands, in order, with `--collect-only` derivations

```
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py --collect-only -q -m requires_live_project
tests/operations/test_issue243_closeproject_probe.py::test_p1_mode_matrix
tests/operations/test_issue243_closeproject_probe.py::test_p2_depth_table
tests/operations/test_issue243_closeproject_probe.py::test_p2_public_surface_matches_depth_table
tests/operations/test_issue243_closeproject_probe.py::test_p3_p6_reproduction_and_symptom
tests/operations/test_issue243_closeproject_probe.py::test_p4_control_run_normal_close
tests/operations/test_issue243_closeproject_probe.py::test_p5_save_before_forced_end
6 tests collected in 0.14s
```

```
$ python -m pytest tests/operations/test_undoable_mode_live.py --collect-only -q -m requires_live_project
...
33 tests collected in 1.05s
```

```
$ python -m pytest tests/operations/test_target_live_smoke.py --collect-only -q -m requires_live_project
...
3 tests collected in 0.14s
```

```
$ python -m pytest tests/operations/test_transaction_rollback.py --collect-only -q -m requires_live_project
no tests collected (20 deselected) in 0.15s
```

All four counts match the frozen table in `tasks.md` (probe 6, undoable-mode
33, target-smoke 3, rollback 0-live/20-offline).

## Live runs (`FLEXLIBS_REQUIRE_LIVE=1`)

```
$ export FLEXLIBS_REQUIRE_LIVE=1
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s
6 passed, 1 warning in 9.29s
```

```
$ python -m pytest tests/operations/test_undoable_mode_live.py -m requires_live_project -q
33 passed, 1 warning in 17.28s
```

```
$ python -m pytest tests/operations/test_target_live_smoke.py -m requires_live_project -q
3 passed, 4 warnings in 4.50s
```

`tests/live_status.json` after both runs:

```json
"run_mode": "live",
"run_timestamp": "2026-09-07T09:46:02Z"
```

`run_mode` is `"live"` -- this run measured real LCM behaviour, not mocks.

## Offline runs

```
$ python -m pytest tests/operations/test_transaction_rollback.py -q
20 passed, 3 warnings in 1.09s
```

```
$ python -m pytest tests -m "not requires_live_project" -q
1290 passed, 470 deselected, 17 warnings in 12.22s
```

Offline baseline is **unchanged at 1290 passed**, before and after the T3
patch to `CloseProject()`. No offline test exercises the new
`HasOpenSessionTask()`/try-except guard path with a double that would
surface a behaviour change, so this is the expected (not merely hoped-for)
result.

## Before/after survivor-count table

Quoting the unfixed-code ("before") values verbatim from
`evidence/live-cycle1-probe.md`, cycle 1, and the patched-code ("after")
values measured in this run, both re-read from the LCM after a read-only
reopen of the same `.fwdata`.

| Probe | Setup | Forced condition | Before (unfixed, cycle 1) | After (patched, T3/T4, this run) |
|---|---|---|---|---|
| P-3 | 25 `TEST_` entries | manual `EndNonUndoableTask()` before `CloseProject()` | **0/25**, `CloseProject()` raised `Cannot end task that has not been started.` | **25/25**, `CloseProject()` did NOT raise |
| P-4 (control) | 25 entries | none | 25/25 | 25/25 (unchanged, re-confirmed) |
| P-5 | 25 entries | `SaveChanges()` at `CurrentDepth=1`, then forced End | **0/25**, `CloseProject()` raised | **0/25**, `CloseProject()` did NOT raise -- see verdict below |

### P-3 verdict

Fixed exactly as intended: `HasOpenSessionTask()` reads `False` (the
manual End already collapsed the envelope), the guard skips the redundant
`EndNonUndoableTask()`, `CloseProject()` reaches `usm.Save()` without
raising, and all 25 entries survive a read-only reopen. `.fwdata` size
changed (5,158,956 -> 5,179,581 bytes, delta +20,625) and a `Target.bak`
sibling appeared this time -- expected and correct now that `usm.Save()`
actually persists, unlike the unfixed run where nothing was written.

### P-5 verdict -- THREE-OUTCOME MEASUREMENT, RESULT IS THE "0/25" BRANCH

`SaveChanges()`'s own raise is **UNCHANGED**, as required (T3 does not
touch `SaveChanges()`): it still raises
`InvalidOperationException: Commit at wrong place.` at `CurrentDepth=1`,
and `CurrentDepth` still drops from 1 to 0 as a side effect (both measured
live, matching cycle 1 exactly).

What DID change: `CloseProject()` no longer raises. The guard correctly
reads `HasOpenSessionTask()` as `False` after the collapsed envelope,
skips `EndNonUndoableTask()` (which itself still raises
`Cannot end task that has not been started.` when force-called manually,
confirming the envelope really is gone), and reaches `usm.Save()`.

However, the reopen count is **0/25, not 25/25**. This is the "If 0/25"
branch `tasks.md` T4 named in advance, not a partial-fix defect in T3:
**T3's guard behaves exactly as designed** (no raise, reaches `Save()` at
a legal depth) -- the remaining loss is that the `UnitOfWorkService`'s
internal commit/`UndoStack` state, once `SaveChanges()`'s
`CheckReadyForCommit` failure has fired, does not recover for a
subsequent `usm.Save()` call later in the same process. Recorded as a
dated note under `spec.md` Q2 (2026-09-07) and reported prominently in
`reviews/cycle4-programmer.md`. Per the task brief, this is NOT
silently expanded into a `SaveChanges()` guard here -- it sharpens the
existing Q1 follow-up already routed to
`specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user approval".

## PASS/FAIL

**PASS.** All required live suites green with `run_mode: live`
(probe 6/6, undoable-mode 33/33, target-smoke 3/3); rollback suite green
offline (20/20); full offline suite unchanged at 1290 passed. P-3 measures
the guard's intended fix (0/25 -> 25/25). P-5 measures the guard working
correctly in isolation (no raise reached) but exposes a NEW, separately
scoped finding (0/25, not 25/25) that is recorded, not concealed or
silently absorbed into this task's scope.
