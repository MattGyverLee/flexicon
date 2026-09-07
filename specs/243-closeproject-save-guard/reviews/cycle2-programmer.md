# Cycle 2 -- Programmer report: T1 (depth-read surface)

**Members added** (`flexicon/code/FLExProject.py`, inserted between
`CloseProject()` and the `Cache` property, ~line 339 onward):
- `_ReadActionHandlerDepth(self)` -- private helper. Raises `FP_ProjectError`
  when `not hasattr(self, "project")`; otherwise returns
  `self.project.ActionHandlerAccessor.CurrentDepth` verbatim. No
  `except`/`getattr` fallback anywhere in it.
- `CurrentDepth` -- **property** (not a method). Chose property to match the
  `Cache` property precedent (line ~340 pre-edit): a no-argument,
  no-side-effect, discoverable read of raw LCM state. Body is a one-line
  passthrough: `return self._ReadActionHandlerDepth()`.
- `HasOpenSessionTask()` -- method (per task naming with `()`). Calls
  `depth = self._ReadActionHandlerDepth()` FIRST (so closed/never-opened
  raises before the mode check, avoiding an `AttributeError` on `self._undoable`
  when the project was never opened -- `self._undoable` is only ever set
  after `self.project` in `OpenProject()`), then `if self._undoable: return
  False`, else `return depth > 0`.

**No lenient fallback confirmed:** grepped the new code -- zero `except:`,
zero `getattr(..., 0)`, zero isinstance coercion. Verified live that closed
and never-opened both raise `FP_ProjectError` rather than returning 0/False.

**Helper signature and T2:** `_ReadActionHandlerDepth(self)` takes only
`self` and either raises or returns the raw int. T2's three call sites can
wrap `project._ReadActionHandlerDepth()` (or the module-owning project's
private call) in their own local `try/except`/`getattr` exactly as today,
so the signature permits T2's wrapped-delegation shape without modification.

**Q3 note:** no `flexicon.CAPABILITIES` token added (per the frozen Q3
ruling in the dispatch). No consumer encountered in this pass that could not
use `hasattr(project, "HasOpenSessionTask")`; nothing to route to QUEUE.md.

**P-2 conformance:** all 8 frozen P-2 rows re-read live via the new
`CurrentDepth`/`HasOpenSessionTask()` surface agree exactly with the frozen
table, including `HasOpenSessionTask()==False` at depth 1 inside
`UndoableOperation()` (C3). Both new raise cases (a) post-`CloseProject()`
and (b) never-opened both raised `FP_ProjectError` with message "Cannot read
action handler depth: project is not open." No disagreements found.

**Live run_mode:** `"live"` (`tests/live_status.json`,
`run_timestamp: 2026-09-07T09:12:11Z`), sandbox-only, real Target untouched.

**Extended probe:** 6/6 passing (5 pre-existing + new
`test_p2_public_surface_matches_depth_table`).

**Offline suite:** 1290 passed, 470 deselected -- identical to pre-T1
baseline, zero regression.

Evidence: `specs/243-closeproject-save-guard/evidence/live-t1-depth-read-surface.md`.
Scope fences respected: `CloseProject()` (T3), `SaveChanges()` (untouched),
`transaction.py`/`undoable_operation.py`/`System/CustomFieldOperations.py`
(untouched), no `CAPABILITIES` token, no GitHub issues filed.
