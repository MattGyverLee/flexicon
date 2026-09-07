# Evidence -- T8a / P-10: SaveChanges() depth blast radius (issue #243)

Date: 2026-09-07 (spurt 6, cycle 6)
Fixture: `target_sandbox_path` ONLY. The real Target project was never
opened; no `scripts/restore_*.py` was run.
No file under `flexicon/` was touched -- see the `git diff --stat --
flexicon/` output below (empty). Only
`tests/operations/test_issue243_closeproject_probe.py` was extended, plus
this evidence file and the cycle-6 report.

MEASUREMENT ONLY. `SaveChanges()` and `CloseProject()` were not modified,
reordered, or guarded. This task settles what the guard's SHAPE must be for
T8b; it does not implement the guard.

## Commands, in order, with `--collect-only` derivations

The probe file's live-test count grows again here, from 9 (frozen at T6) to
**10** (P-10 added -- one new test function covering three sub-cases A/B/C,
matrix-style like P-1/P-2):

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

10 tests collected in 0.19s
```

## Live run (`FLEXLIBS_REQUIRE_LIVE=1`)

```
$ export FLEXLIBS_REQUIRE_LIVE=1
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s
10 passed, 1 warning in 10.45s
```

`tests/live_status.json` after this run:

```
"run_mode": "live",
"run_timestamp": "2026-09-07T15:59:49Z",
```

`run_mode` is `"live"` -- this run measured real LCM behaviour, not mocks.

## Offline baseline

```
$ unset FLEXLIBS_REQUIRE_LIVE
$ python -m pytest tests -m "not requires_live_project" -q
1290 passed, 474 deselected, 17 warnings in 10.97s
```

Unchanged at **1290 passed** (the frozen baseline). Deselected count rose
from 473 (T6's evidence) to 474 -- exactly the +1 new `requires_live_project`
test (`test_p10_savechanges_depth_blast_radius`, which itself covers three
sub-cases inside one test function, matrix-style like P-1/P-2), not a
regression.

## Scope fence check

```
$ git diff --stat -- flexicon/
(empty)
$ git diff --stat -- tests/operations/test_issue243_closeproject_probe.py
 tests/operations/test_issue243_closeproject_probe.py | 385 +++++++++++++++++++++
 1 file changed, 385 insertions(+)
```

No file under `flexicon/` was touched. `SaveChanges()`, `Transaction()`,
`UndoableOperation()`, and `CloseProject()` are observed only, called
through `FLExProject`'s own public API exactly as an application would call
them.

(Unrelated to this task: `git status` also shows pending changes to
`CHANGELOG.md`, `specs/243-closeproject-save-guard/spec.md`, a deleted
`.claude/ralph-loop.local.md`, and an untracked
`specs/243-closeproject-save-guard/reviews/cycle6-doc.md` -- these were
already present before this task started and were made by a different
crew member in this same cycle, not by this task. Not touched here.)

---

## The three measured cases

All three cases use the same design: open a sandbox project, create 25
`TEST_p10<x>_`-prefixed entries, enter the named context manager, read
`CurrentDepth` immediately before calling `SaveChanges()`, call it via the
harness's `_safe()` wrapper (so any raised exception is caught inside the
wrapper and never escapes the `with` block -- this matters for
`UndoableOperation()`, which is genuinely transactional and would otherwise
treat an escaping exception as a rollback trigger, conflating "what
SaveChanges() did" with "what the block did in response to an unrelated
failure"), read `CurrentDepth` immediately after, re-read the survivor count
from the STILL-OPEN project (before the block's own `__exit__` runs), exit
the block normally, `CloseProject()`, then reopen the same `.fwdata`
read-only in a separate step and re-count all three prefixes on disk.

### Verbatim `[PROBE]` console lines

```
[PROBE][P10] (A: undoable=True, inside UndoableOperation()) created 25 entries with prefix 'TEST_p10a_'
[PROBE][P10] (A: undoable=True, inside UndoableOperation()) CurrentDepth before SaveChanges(): 1
[PROBE] P10 (A: undoable=True, inside UndoableOperation()) SaveChanges(): RAISED InvalidOperationException: Commit at wrong place.
   at SIL.LCModel.Infrastructure.Impl.UndoStack.CheckReadyForCommit(String message)
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.SaveInternal()
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.Save()
[PROBE] P10 (A: undoable=True, inside UndoableOperation()) CurrentDepth after SaveChanges(): OK -> 0
[PROBE][P10] (A: undoable=True, inside UndoableOperation()) CurrentDepth after SaveChanges(): 0
[PROBE][P10] (A: undoable=True, inside UndoableOperation()) survivor count re-read from the STILL-OPEN project (inside the block, before its __exit__): 25 / 25
[PROBE] P10 case A CloseProject: OK -> None
[PROBE][P10] (B: undoable=True, inside Transaction()) created 25 entries with prefix 'TEST_p10b_'
[PROBE][P10] (B: undoable=True, inside Transaction()) CurrentDepth before SaveChanges(): 0
[PROBE] P10 (B: undoable=True, inside Transaction()) SaveChanges(): OK -> None
[PROBE] P10 (B: undoable=True, inside Transaction()) CurrentDepth after SaveChanges(): OK -> 0
[PROBE][P10] (B: undoable=True, inside Transaction()) CurrentDepth after SaveChanges(): 0
[PROBE][P10] (B: undoable=True, inside Transaction()) survivor count re-read from the STILL-OPEN project (inside the block, before its __exit__): 25 / 25
[PROBE] P10 case B CloseProject: OK -> None
[PROBE][P10] (C: undoable=False, inside Transaction()) created 25 entries with prefix 'TEST_p10c_'
[PROBE][P10] (C: undoable=False, inside Transaction()) CurrentDepth before SaveChanges(): 1
[PROBE] P10 (C: undoable=False, inside Transaction()) SaveChanges(): RAISED InvalidOperationException: Commit at wrong place.
   at SIL.LCModel.Infrastructure.Impl.UndoStack.CheckReadyForCommit(String message)
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.SaveInternal()
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.Save()
[PROBE] P10 (C: undoable=False, inside Transaction()) CurrentDepth after SaveChanges(): OK -> 0
[PROBE][P10] (C: undoable=False, inside Transaction()) CurrentDepth after SaveChanges(): 0
[PROBE][P10] (C: undoable=False, inside Transaction()) survivor count re-read from the STILL-OPEN project (inside the block, before its __exit__): 0 / 25
[PROBE] P10 case C CloseProject: OK -> None
[PROBE][P10] (A: undoable=True, inside UndoableOperation()) survivor count after a genuine close-and-reopen: 25 / 25
[PROBE][P10] (B: undoable=True, inside Transaction()) survivor count after a genuine close-and-reopen: 25 / 25
[PROBE][P10] (C: undoable=False, inside Transaction()) survivor count after a genuine close-and-reopen: 0 / 25
[PROBE] P10 reopen CloseProject: OK -> None
[PROBE][P10] VERDICT: A(UndoableOperation,undoable=True,depth=1): SaveChanges() RAISED, in_memory=25/25, on_disk=25/25 || B(Transaction,undoable=True,depth=0): SaveChanges() SUCCEEDED, in_memory=25/25, on_disk=25/25 || C(Transaction,undoable=False,depth=1): SaveChanges() RAISED, in_memory=0/25, on_disk=0/25
[PROBE][P10] CASE A VERDICT (MEASURED, third outcome -- distinct from both named alternatives above): SaveChanges() RAISED the identical 'Commit at wrong place.' string used by the destructive undoable=False mechanism, YET the edit was NOT destroyed -- 25/25 survived in-memory (still-open, before the block's own __exit__) AND 25/25 survived a genuine close-and-reopen. The survival does not depend on this SaveChanges() call: the UndoableOperation() block's own normal __exit__ (no exception escaped, because _safe() caught it) commits the edit onto the real UndoableUnitOfWorkHelper stack regardless, and CloseProject()'s own later usm.Save() at the now-collapsed depth 0 persists it for real. VERDICT: BLANKET GUARD SAFE for this case -- the call already fails today (just with LCM's cryptic message instead of the guard's own clearer one), and the edit was never actually at risk from this specific SaveChanges() call one way or the other, so refusing it earlier sacrifices nothing.
```

### Six-item table

| # | Item | Case A: `undoable=True`, inside `UndoableOperation()` | Case B: `undoable=True`, inside `Transaction()` | Case C: `undoable=False`, inside `Transaction()` |
|---|------|------|------|------|
| 1 | Mode / exact context | undoable=True; `with project.UndoableOperation("p10 probe"):` | undoable=True; `with project.Transaction("p10 probe"):` | undoable=False; `with project.Transaction("p10 probe"):` |
| 2 | `CurrentDepth` immediately BEFORE `SaveChanges()` | **1** | **0** | **1** |
| 3 | Did `SaveChanges()` raise? | **YES** -- `InvalidOperationException: Commit at wrong place.` (identical stack trace to P-5/P-7/P-9's undoable=False trigger) | **NO** -- returned `None` | **YES** -- `InvalidOperationException: Commit at wrong place.` (identical stack trace) |
| 4 | `CurrentDepth` immediately AFTER | 0 | 0 | 0 |
| 5 | Survivor count, STILL-OPEN project (in-memory, P-7 technique, read before the block's `__exit__`) | **25 / 25** | 25 / 25 | **0 / 25** |
| 6 | Survivor count, genuine close-and-reopen (on-disk) | **25 / 25** | 25 / 25 | **0 / 25** |

## Interpretation

**Case B confirms, by direct measurement (not by citing the frozen P-2/T1
table), that `Transaction()` does not itself change `CurrentDepth` in
either mode.** Under `undoable=True`, `Transaction()`'s depth-0 context is
indistinguishable from the bare undoable=True session: `SaveChanges()`
succeeds outright, no exception, and the edit persists. A `CurrentDepth > 0`
guard never fires here at all -- this case is entirely outside the guard's
domain.

**Case C reproduces the already-understood destructive mechanism exactly**
(P-5/P-7): `Transaction()` under `undoable=False` is depth-1, matching the
bare undoable=False session-long envelope. `SaveChanges()` raises the
owner's exact symptom string and the change set is gone even before
`CloseProject()` is ever entered (0/25 in-memory, confirmed again 0/25 on
disk). A blanket guard here prevents damage that currently happens.

**Case A is the headline finding, and it is a THIRD outcome distinct from
both alternatives named in the task brief.** `SaveChanges()` raises the
identical `"Commit at wrong place."` exception used by the destructive
mechanism (Case C) -- so it does **not** "succeed" in any sense that a
guard could be accused of blocking a working call. But unlike Case C, the
edit is **not destroyed**: it survives both in-memory (25/25, read before
the block's own exit) and after a genuine close-and-reopen (25/25). The
mechanism: because no exception escaped the `with` block (the harness's
`_safe()` wrapper caught it, exactly to isolate this measurement),
`UndoableOperation()`'s own `__exit__` ran its normal, non-rollback path --
`UndoableUnitOfWorkHelper`'s `RollBack` flag stays `False` on a clean exit --
and committed the pending edit onto the real undo stack regardless of what
the mid-block `SaveChanges()` call did. `CloseProject()`'s own later
`usm.Save()`, reached at the now-collapsed depth 0, then persists it for
real, independently of the failed mid-block call.

## PASS/FAIL line

**PASS.** All 10 live tests green, `run_mode: live` confirmed, offline
baseline unchanged at 1290 passed (deselected 473 -> 474, exactly +1), `git
diff --stat -- flexicon/` empty, `SaveChanges()` and `CloseProject()`
untouched. See `reviews/cycle6-programmer.md` for the guard-shape verdict.
