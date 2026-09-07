# Evidence -- T8b: SaveChanges() depth guard (issue #243)

Date: 2026-09-07 (spurt 7, cycle 7)
Fixture: `target_sandbox_path` ONLY. The real Target project was never
opened; no `scripts/restore_*.py` was run.

Scope: `flexicon/code/FLExProject.py` (`SaveChanges()` guard + three
docstring corrections), plus the 11 enumerated test-blast-radius sites and
the new P-11 probe. `CloseProject()`'s logic was NOT touched (T7 is a
separate, later task). `CHANGELOG.md`, `spec.md`, `tasks.md`, `QUEUE.md` are
owned by a parallel `/lex-doc` task this cycle and are untouched here (see
"Scope fence check" below).

## Scope fence check

```
$ git diff --stat -- flexicon/ tests/manual_verification.py \
    tests/operations/test_abort_session_live.py \
    tests/operations/test_issue243_closeproject_probe.py \
    tests/test_transaction_honesty.py
 flexicon/code/FLExProject.py                       | 109 ++-
 tests/manual_verification.py                       |   7 +-
 tests/operations/test_abort_session_live.py        |  50 +-
 tests/operations/test_issue243_closeproject_probe.py | 952 ++++++++++++---
 tests/test_transaction_honesty.py                  |  14 +-
 5 files changed, 982 insertions(+), 150 deletions(-)
```

`git status --short` also shows pre-existing, not-mine modifications to
`CHANGELOG.md`, `specs/243-closeproject-save-guard/spec.md`,
`specs/243-closeproject-save-guard/tasks.md`,
`specs/tier1-silent-data-loss/QUEUE.md`, a deleted
`.claude/ralph-loop.local.md`, and untracked cycle-6/cycle-7 review files
from other crew members this cycle -- none of these were touched by this
task.

## The guard (C21)

`FLExProject.SaveChanges()` now reads `self.CurrentDepth` (the T1 public
surface, not a fresh `getattr` on the action handler) immediately after the
`writeEnabled` check and before `self.ObjectRepository(IUndoStackManager)`.
If depth > 0 it raises `FP_TransactionError` with a mode-differentiated
message (per `self._undoable`) and `usm.Save()` is never called. If the
depth read itself raises, the guard fails OPEN: logs a `WARNING` and falls
through to `usm.Save()` exactly as before the guard existed.

## Docstring corrections

1. `SaveChanges()` -- added `Raises: FP_TransactionError`, made both
   Examples mode-explicit (`undoable=True` example calls `SaveChanges()`
   after the block; `undoable=False` example shows the refusal and routes
   to `CloseProject()` instead).
2. `RefreshFromDisk()` -- Example now pins `undoable=True` explicitly, with
   a "Note on mode" stating the depth contract only (per the ANTI-OVERCLAIM
   instruction): `SaveChanges()` raises at depth > 0 under `undoable=False`
   so it cannot be called mid-session at all, and `CloseProject()` ends the
   envelope first so it reaches `usm.Save()` at a legal depth. Does NOT
   claim `RefreshFromDisk()` + `CloseProject()` recovers a
   pending-reconciliation wedge under `undoable=False` -- that is
   unmeasured.
3. `AbortSession()` -- the `else:` branch of its Example now calls
   `project.CloseProject()` instead of `project.SaveChanges()`, with an
   inline comment explaining why `SaveChanges()` would always raise there
   (`undoable=False`, session-long envelope holds depth at 1).

## Commands, `--collect-only` derivations

```
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project --collect-only -q
tests/operations/test_issue243_closeproject_probe.py::test_p1_mode_matrix
tests/operations/test_issue243_closeproject_probe.py::test_p2_depth_table
tests/operations/test_issue243_closeproject_probe.py::test_p2_public_surface_matches_depth_table
tests/operations/test_issue243_closeproject_probe.py::test_p3_p6_reproduction_and_symptom
tests/operations/test_issue243_closeproject_probe.py::test_p4_control_run_normal_close
tests/operations/test_issue243_closeproject_probe.py::test_p5_save_before_forced_end
tests/operations/test_issue243_closeproject_probe.py::test_p7_data_survives_failed_savechanges_in_memory
tests/operations/test_issue243_closeproject_probe.py::test_p8_fresh_entry_after_failed_savechanges
tests/operations/test_issue243_closeproject_probe.py::test_p9_iundostackmanager_detector
tests/operations/test_issue243_closeproject_probe.py::test_p10_savechanges_depth_blast_radius
tests/operations/test_issue243_closeproject_probe.py::test_p11_case_a_exception_propagates_and_rolls_back

11 tests collected in 0.14s
```

Growth: 10 (T8a) -> **11** (P-11 added, one new live test function).

```
$ python -m pytest tests/operations/test_abort_session_live.py -m requires_live_project --collect-only -q
... (12 tests, unchanged count -- test_save_changes_raises_commit_at_wrong_place
     was rewritten in place, not added)
12 tests collected in 1.02s
```

## Live runs (`FLEXLIBS_REQUIRE_LIVE=1`)

```
$ export FLEXLIBS_REQUIRE_LIVE=1
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q
11 passed, 1 warning in 13.19s

$ python -m pytest tests/operations/test_abort_session_live.py -m requires_live_project -q
12 passed, 12 warnings in 7.37s
```

`tests/live_status.json` after these runs:

```
"run_mode": "live",
"run_timestamp": "2026-09-07T16:40:09Z",
```

## Offline baseline

```
$ unset FLEXLIBS_REQUIRE_LIVE
$ python -m pytest tests -m "not requires_live_project" -q
1290 passed, 475 deselected, 17 warnings in 10.91s
```

**1290 passed** (unchanged from the frozen baseline). Deselected rose from
474 (T8a) to **475** -- exactly +1 for the new `test_p11_...` live test, not
a regression. (First run after widening `test_transaction_honesty.py`'s
slice window failed with the window still too narrow at 1000/2500 chars;
both windows were widened -- `save_body` to 6000, `refresh_body` to 4000 --
and the suite went green. See "Item 10" below.)

## Item-by-item disposition of the 11 enumerated test sites

1. **`test_abort_session_live.py:234-266`
   `TestSaveChangesIsUnusableInThisMode::test_save_changes_raises_commit_at_wrong_place`**
   -- INVERTED. Now asserts `FP_TransactionError` (not
   `System.InvalidOperationException`), asserts `"CurrentDepth"` appears in
   the message, and asserts the pending create SURVIVES in the still-open
   project (proof `usm.Save()` was never reached). Class docstring rewritten
   from "PRE-EXISTING DEFECT ... must be inverted" to "FIXED ... this is the
   inversion". PASSED live.
2. **`test_abort_session_live.py:121-123`** -- prose cross-reference updated
   ("cannot be used to commit" -> "refuses to commit ... issue #243 depth
   guard, spec.md C21").
3. **P-5 `:593-606`** -- now asserts `FP_TransactionError`, asserts
   `"Commit at wrong place."` is ABSENT from the message, and asserts
   `CurrentDepth` stays UNCHANGED at 1 across the refused call (proof
   `usm.Save()` was never reached).
4. **P-5 `:658` `surviving_count`** -- flipped from `== 0` to `== N_ENTRIES`.
   MEASURED: **25/25**, matching the prediction (see "P-5 measured result"
   below) -- NOT tuned to an observed surprise, the prediction held.
5. **P-5 `:568-580`/`:608-635` verdict prose** -- reworded for the new
   contract (the manual `End` now succeeds against a genuinely-still-open
   envelope rather than "forcing" a double-end).
6/7/8. **P-7 (`:693-760`), P-8 (`:817-894`), P-9 (`:1029-1058`, both calls)**
   -- trigger switched from `project.SaveChanges()` to the raw
   `ObjectRepository(IUndoStackManager)` + `usm.Save()` accessor.
   Pre-existing assertions (`"Commit at wrong place."`, 0/25, detector
   readings) are UNCHANGED and still TRUE -- all three passed live. Each
   gained a "T8b note" docstring paragraph explaining the raw-call
   substitution.
9. **P-10** -- Case A: now expects `FP_TransactionError`
   (not the raw liblcm string), `CurrentDepth` unchanged at 1, survivors
   **25/25 both reads** (MEASURED, matches T8a's data-outcome prediction).
   Case C: now expects `FP_TransactionError`, `CurrentDepth` unchanged at 1,
   survivors **25/25 both reads** (MEASURED -- this is the changed
   prediction from T8a's pre-guard 0/25; the T8a evidence file's table is
   the frozen "before" column, unedited). Case B: entirely unchanged --
   depth 0, no guard involvement, `SaveChanges()` succeeds normally,
   25/25 both reads.
10. **`test_transaction_honesty.py:73`** (now `:82`) -- `save_body` window
    widened from 1000 to 6000 chars; `refresh_body` (a different line, not
    named in the brief but broken by the same cause) ALSO needed widening
    from 2500 to 4000, because `RefreshFromDisk()`'s docstring grew too.
    Both widened with an explanatory comment; the assertion's intent
    (both methods resolve the same accessor) is unchanged.
11. **`tests/manual_verification.py:487,526`** -- line 526's finding string
    updated to note the new refusal contract (cheap, prose-only). Line 487
    left as-is (pure availability check, not affected by the guard).

## P-5 measured result (headline)

```
[PROBE][P5] CurrentDepth before SaveChanges(): 1
[PROBE][P5] CurrentDepth after SaveChanges() attempt: 1
[PROBE][P5] SaveChanges() now refuses BEFORE usm.Save() (T8b): FP_TransactionError: SaveChanges() refused: CurrentDepth is 1 (the session-long non-undoable envelope opened by OpenProject(undoable=False) is still open). usm.Save() was NOT attempted, so this refusal itself discarded nothing -- ...
[PROBE][P5] TEST_ entries surviving, re-read from LCM: 25 / 25
[PROBE][P5] GO/NO-GO VERDICT (T8b guard, measured not assumed): 25/25 survived -- MATCHES the T8b prediction
```

**Survivor count: 25/25 (N_ENTRIES/N_ENTRIES). This is the PREDICTED value,
NOT the pre-guard T4 measurement (0/25) -- no flag needed; the prediction
held.** Mechanism: the guard refuses `SaveChanges()` before it ever calls
`usm.Save()`, so the session-long envelope is left genuinely open (depth
unchanged at 1). The manual "forced" `EndNonUndoableTask()` call -- which
pre-guard found nothing to end (`Cannot end task that has not been
started.`) because the envelope was already collapsed by the failed raw
`usm.Save()` -- now finds a genuinely open envelope and ends it
successfully, functionally identical to `CloseProject()`'s own normal
Phase-1 End. `CloseProject()` then finds `HasOpenSessionTask()` False,
skips its own End, and reaches `usm.Save()` at a legal depth with an intact,
never-touched change set.

## Phase-1 `else:` branch observation (for T7's C23 recut -- NOT acted on here)

With `--log-cli-level=DEBUG` on the P-5 test:

```
[PROBE] P5 manual EndNonUndoableTask (post-SaveChanges): OK -> None
DEBUG flexicon.code.FLExProject:FLExProject.py:369 CloseProject: HasOpenSessionTask() is False; skipping EndNonUndoableTask() rather than assuming the mode implies the envelope is present.
[PROBE] P5 CloseProject (expected to succeed, guard finds envelope already ended): OK -> None
```

**Yes, `CloseProject()` took the Phase-1 `else:` branch** (the
`HasOpenSessionTask()` False, `EndNonUndoableTask()` skipped, `debug`-level
log path from T3/C6). **Yes, the save succeeded** -- `CloseProject()`
returned `None` (no raise) and the reopen confirmed 25/25 persisted. Under
T8b this Phase-1-`else:` branch is no longer anomalous the way C14 describes
for the pre-guard P-5 chain -- here it is reached because the guard's own
manual-End call cleanly ended a genuinely-open envelope, not because an
unguarded `SaveChanges()` collapsed it as a side effect. Recorded verbatim
per the task brief; `CloseProject()` was not modified and this observation
is input to T7's own future recut, not acted on here.

## P-10 full six-item table, with a before/after column

`before` = T8a evidence (`evidence/live-t8a-savechanges-depth-blast-radius.md`,
pre-guard, frozen, unedited). `after` = this task's live measurement,
post-guard.

| # | Item | Case A (before -> after) | Case B (before -> after) | Case C (before -> after) |
|---|------|------|------|------|
| 1 | Mode / context | undoable=True, `UndoableOperation()` (unchanged) | undoable=True, `Transaction()` (unchanged) | undoable=False, `Transaction()` (unchanged) |
| 2 | `CurrentDepth` BEFORE | 1 -> 1 | 0 -> 0 | 1 -> 1 |
| 3 | Did `SaveChanges()` raise? | YES (raw `InvalidOperationException: Commit at wrong place.`) -> YES (`FP_TransactionError`, guard's own message, NOT the raw string) | NO -> NO | YES (raw `InvalidOperationException`) -> YES (`FP_TransactionError`) |
| 4 | `CurrentDepth` AFTER | 0 (collapsed as liblcm side effect) -> **1 (UNCHANGED -- guard never touches LCM state)** | 0 -> 0 | 0 (collapsed) -> **1 (UNCHANGED)** |
| 5 | Survivor count, STILL-OPEN (in-memory) | 25/25 -> 25/25 (unchanged) | 25/25 -> 25/25 | **0/25 -> 25/25 (CHANGED -- guard leaves change set intact)** |
| 6 | Survivor count, close-and-reopen (on-disk) | 25/25 -> 25/25 (unchanged) | 25/25 -> 25/25 | **0/25 -> 25/25 (CHANGED)** |

Verbatim post-guard console lines:

```
[PROBE][P10] TABLE A: undoable=True, inside UndoableOperation(): depth_before=1, save_raised='FP_TransactionError: SaveChanges() refused: CurrentDepth is 1 (a unit of work is currently open). usm.Save() was NOT attempted, so this refusal itself discarded nothing. ...', depth_after=1, in_memory_count=25/25, on_disk_count=25/25, CloseProject_raised=None
[PROBE][P10] TABLE B: undoable=True, inside Transaction(): depth_before=0, save_raised=None, depth_after=0, in_memory_count=25/25, on_disk_count=25/25, CloseProject_raised=None
[PROBE][P10] TABLE C: undoable=False, inside Transaction(): depth_before=1, save_raised="FP_TransactionError: SaveChanges() refused: CurrentDepth is 1 (the session-long non-undoable envelope opened by OpenProject(undoable=False) is still open). usm.Save() was NOT attempted, so this refusal itself discarded nothing -- your pending changes are intact in memory and will be written to disk by CloseProject(). ...", depth_after=1, in_memory_count=25/25, on_disk_count=25/25, CloseProject_raised=None
[PROBE][P10] VERDICT: A(UndoableOperation,undoable=True,depth=1): SaveChanges() RAISED, in_memory=25/25, on_disk=25/25 || B(Transaction,undoable=True,depth=0): SaveChanges() SUCCEEDED, in_memory=25/25, on_disk=25/25 || C(Transaction,undoable=False,depth=1): SaveChanges() RAISED, in_memory=25/25, on_disk=25/25
```

## P-11 -- NEW live case (10 -> 11)

Design: P-10 case A repeated, but `project.SaveChanges()` is called
DIRECTLY inside `with project.UndoableOperation("p11 probe"):` (not wrapped
in `_safe()`), letting the guard's `FP_TransactionError` PROPAGATE out of
the `with` block, exercising `UndoableOperation()`'s own exception-triggered
rollback path (`set_RollBack(True)` + `Dispose()`).

**A-priori prediction (recorded in the docstring before running): 0/25**
survivors -- on the assumption that an escaping exception's rollback
discards the block's mutations, identical to what an uncaught raw liblcm
exception would already have done in this mode pre-T8b.

**MEASURED LIVE -- CONTRADICTS THE PREDICTION. This is a P0 FINDING,
reported verbatim, NOT tuned to match:**

```
[PROBE][P11] CurrentDepth before UndoableOperation() block: 0
[PROBE][P11] CurrentDepth inside UndoableOperation() block: 1
[PROBE][P11] FP_TransactionError PROPAGATED out of the UndoableOperation() block, as expected: SaveChanges() refused: CurrentDepth is 1 (a unit of work is currently open). usm.Save() was NOT attempted, so this refusal itself discarded nothing. ...
[PROBE][P11] CurrentDepth after the block's own rollback exit: 0
[PROBE][P11] TEST_ entries still visible in the STILL-OPEN project after the block rolled back: 25 / 25
[PROBE][P11] TEST_ entries surviving a genuine close-and-reopen: 25 / 25
[PROBE][P11] VERDICT: FP_TransactionError propagated out of UndoableOperation(), Dispose()/set_RollBack(True) ran (per the debug log) -- in_memory=25/25, on_disk=25/25. P0 FINDING: CONTRADICTS the a-priori 0/25 rollback prediction
```

The debug log independently confirms `set_RollBack(True)` and `Dispose()`
ran:

```
WARNING flexicon.code.undoable_operation:undoable_operation.py:154 UndoableOperation 'p11 probe': exception FP_TransactionError, UnitOfWork rolled back
```

**Yet all 25 created entries survived, both in-memory (re-read from the
still-open project before `CloseProject()`) and on-disk (after a genuine
close-and-reopen).** This means `UndoableUnitOfWorkHelper.Dispose()` with
`RollBack=True` did NOT, in this measured case, discard the object creations
made inside the block, despite `transaction.py`'s and
`undoable_operation.py`'s own docstrings both asserting that it does.

**This is NOT a regression introduced by the T8b guard.** The guard raised
and refused correctly (`CurrentDepth` unchanged inside the block at
measurement time, `FP_TransactionError` propagated as expected). The finding
is about what liblcm's OWN rollback primitive
(`UndoableUnitOfWorkHelper.Dispose()`/`set_RollBack`) does afterward,
independent of what triggered the exception -- the SAME exit path already
ran on ANY escaping exception before T8b existed (e.g. the raw liblcm
`InvalidOperationException` this call used to raise pre-guard, if a caller
also failed to catch it). Distinguishing exactly why (e.g. whether object
creation reflects into the cache's live collections in a way `RollBack`
does not reach, versus modified property values which may behave
differently) needs instrumentation inside liblcm/`UnitOfWorkHelper.cs` and
is OUT OF SCOPE for this task.

**Binding consequence for the docstrings (per the task brief's own
constraint): the shipped `undoable=True` `SaveChanges()` docstring does NOT
describe this outcome from inference and is NOT contradicted by this
finding** -- it only states that the block "commits automatically when it
exits normally," which says nothing about a non-normal exit. This measured
surprise must not be used to justify any FUTURE claim that "an escaping
exception safely discards the edit" -- per this measurement, that claim
would be FALSE.

The test asserts the MEASURED value (25/25 both reads), per this file's own
established convention (P-5/P-7/P-8/P-9/P-10: "assert the MEASURED value,
not the hoped-for one"), with the contradiction prominently documented in
the test's own docstring and assertion messages so a future reader is not
re-surprised.

## PASS/FAIL line

**PASS**, with one prominent P0 finding flagged for `/lex-lead` routing
(P-11's escaping-exception rollback not actually discarding data -- a
liblcm-mechanism finding, not a guard defect). All 11 live tests in the
probe file green, all 12 live tests in `test_abort_session_live.py` green,
`run_mode: live` confirmed twice, offline baseline 1290 passed (deselected
474 -> 475, exactly +1), `git diff --stat` confirms the scope fence was
honoured (only `flexicon/code/FLExProject.py` and the enumerated test files
touched), `CloseProject()`'s logic untouched.
