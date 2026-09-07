# Live evidence -- T1: depth-read surface (`CurrentDepth` / `HasOpenSessionTask()`)

Issue #243, `specs/243-closeproject-save-guard/spec.md` C2-C5.

## Commands run

Live probe (extended `test_issue243_closeproject_probe.py`, adds
`test_p2_public_surface_matches_depth_table`):

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s
```

Result: **6 passed** (the 5 pre-existing cycle-1 probes unchanged, plus the
new T1 test), `1 warning` (unrelated `flexlibs2` deprecation alias notice).

Offline regression check (must show zero delta -- T1 only adds members):

```
python -m pytest tests -m "not requires_live_project" -q
```

Result: **1290 passed, 470 deselected** -- identical pass count to the
pre-T1 baseline. No collisions, no regressions.

## run_mode

`tests/live_status.json` -> `"run_mode": "live"` (`run_timestamp:
2026-09-07T09:12:11Z`). This is a genuine live run against the
`target_sandbox_path` fixture (tempdir copy of the Target `.fwbackup`); the
real Target project was never opened. Not mock mode.

## P-2 table conformance -- frozen table vs. live re-read via the NEW public surface

Each value below was read live via `project.CurrentDepth` /
`project.HasOpenSessionTask()` (not the raw `_depth()` helper the original
P-2 probe used), inside `test_p2_public_surface_matches_depth_table`.

| Moment | Frozen `CurrentDepth` (spec.md P-2) | Live `CurrentDepth` | Live `HasOpenSessionTask()` | Agrees? |
|---|---|---|---|---|
| After `OpenProject(undoable=False)` | 1 | 1 | True | YES |
| After `OpenProject(undoable=True)` | 0 | 0 | False | YES |
| Inside `Transaction()` block, `undoable=False` | 1 | 1 | True | YES |
| Inside `Transaction()` block, `undoable=True` | 0 | 0 | False | YES |
| Inside `UndoableOperation()` block, `undoable=True` | 1 | 1 | False (C3: unconditional under `_undoable=True`) | YES |
| After `AbortSession()` returns `True`, `undoable=False` | 1 | 1 | True | YES |
| Immediately after manual `EndNonUndoableTask()`, `undoable=False` | 0 | 0 | False | YES |
| Read-only project | 0 (no exception) | 0 (no exception) | False (no exception) | YES |

**Two new cases (not in the original P-2 probe), both required by C4:**

| Case | Expected | Live result | Agrees? |
|---|---|---|---|
| (a) `CurrentDepth` after a SUCCESSFUL `CloseProject()` | raise `FP_ProjectError` | RAISED `FP_ProjectError: Cannot read action handler depth: project is not open.` | YES |
| (a) `HasOpenSessionTask()` after a SUCCESSFUL `CloseProject()` | raise `FP_ProjectError` | RAISED `FP_ProjectError: Cannot read action handler depth: project is not open.` | YES |
| (b) `CurrentDepth` on a never-opened `FLExProject()` | raise `FP_ProjectError` | RAISED `FP_ProjectError: Cannot read action handler depth: project is not open.` | YES |
| (b) `HasOpenSessionTask()` on a never-opened `FLExProject()` | raise `FP_ProjectError` | RAISED `FP_ProjectError: Cannot read action handler depth: project is not open.` | YES |

No row disagreed with the frozen table. No live regression found.

## PASS/FAIL

**PASS.** `run_mode: live`; extended probe file 6/6 passing; offline suite
1290/1290 passing (zero delta vs. pre-T1); every P-2 row plus both new
closed/never-opened raise cases match the frozen contract exactly, re-read
from the live LCM through the new public `CurrentDepth`/`HasOpenSessionTask()`
surface.
