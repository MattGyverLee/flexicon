# Explore sweep — sharing-based vs depth-based refusals (Cycle 6, issue #243)

**Persisted by:** main session (Explore has no Write tool).

## CATEGORY A — shared / exclusive-access predicated

Only three code sites; none of them tests "is this project shared" or "do I have exclusive access". Everything else matching the search terms is prose, `Shared/` package imports, or the word "block" in comments.

- `flexicon/code/exceptions.py:35-41` — `FP_FileLockedError`, message text tells the user to turn on the FLEx Sharing option. **Actual refusal** (exception class), but its predicate is LCM's own `LcmFileLockedException`, not a flexicon check.
- `flexicon/code/FLExProject.py:247-248` — `except LcmFileLockedException: raise FP_FileLockedError()` inside `OpenProject()`. **Actual refusal**, translated from liblcm; flexicon evaluates no sharing predicate itself.
- `flexicon/code/headless_ui.py:125-146` — `ConflictingSave()`: `logger.error("ConflictingSave: another client saved changes ...")` then `if self._raise_on_conflicting_save: raise FP_ConflictingSaveError(...)`; returns `False` otherwise. **Warning + conditional refusal**, driven by an LCM callback, opt-out via constructor flag. `exceptions.py:92-109` documents it.
- `flexicon/code/headless_ui.py:172-178` (`Retry`) and `180-189` (`OfferToRestore`) — return `False`, log warnings; `Retry`'s docstring mentions "a locked file". **Warnings only**, not shared-project predicates.
- `flexicon/code/FLExProject.py:231-236, 758-803` (`RefreshFromDisk` docstring), `FLExProject.py:766-777` — **documentation** of the shared-mode/reconciliation wedge. `RefreshFromDisk()` itself only guards `writeEnabled`.
- `flexicon/code/Discourse/ConstChartMarkerOperations.py:233-253` — `raise NotImplementedError` because the ChartMarkers list is "project-wide ... every chart in the project shares". **Actual refusal**, but "shares" means shared *within* the project, not multi-user; not a Category A predicate.

## CATEGORY B — transaction-depth / open-UnitOfWork predicated

| file:line | predicate | outcome | fires in |
|---|---|---|---|
| `FLExProject.py:927-929` (`AbortSession`) | `action_handler.CurrentDepth == 0` | `log.debug` + `return False` | undoable=True between ops (depth 0); never in undoable=False |
| `FLExProject.py:931-941` (`AbortSession`) | `self._undoable` (reached only when depth > 0) | raises `FP_TransactionError` | undoable=True inside an UndoableOperation |
| `FLExProject.py:1086-1090` / `1136-1140` | `not self._undoable` | raises `FP_TransactionError` (Undo/Redo) | undoable=False only |
| `FLExProject.py:1094` / `1144` | `not CanUndo()` / `not CanRedo()` | `logger.debug`, no raise | undoable=True |
| `FLExProject.py:349-373` (`CloseProject`) | `if self.HasOpenSessionTask():` else branch | try/except around `EndNonUndoableTask()`; `logger.error` (355-366) or `logger.warning` (369-372); **never blocks `usm.Save()`** | undoable=False (envelope mode) |
| `FLExProject.py:310-312` | `BeginNonUndoableTask()` failure | raises `FP_ProjectError` | undoable=False, at OpenProject |
| `FLExProject.py:390-420`, `423-461`, `464-500` | `_read_depth` / `CurrentDepth` property / `HasOpenSessionTask()` | read-only accessors, no raise | both |
| `System/CustomFieldOperations.py:305-323` (`CreateField`) | `getattr(action_handler,"CurrentDepth",0) > 0` | raises `FP_TransactionError` (cites `UndoStack.CheckNotProcessingDataChanges`) | undoable=False always; undoable=True only inside a UoW |
| `System/CustomFieldOperations.py:328-333` | unconditional fallthrough (depth 0 path) | raises `FP_TransactionError` (not implemented) | undoable=True between ops |
| `undoable_operation.py:92-99` | `not self._project._undoable` | raises `FP_TransactionError` | undoable=False |
| `undoable_operation.py:101-114` | `depth > 0` | `logger.debug` JOIN, no raise | undoable=True nested |
| `undoable_operation.py:86-90` | `not writeEnabled` | raises `FP_ReadOnlyError` | both |
| `transaction.py:95-107` (`_TransactionCM`) | `depth > 0` | `logger.debug` JOIN, no raise | undoable=True nested |
| `transaction.py:175-190` | `_current_depth` helper, returns 0 on failure | no raise | both |
| `FLExProject.py:823-866`, `BaseOperations.py:2223-2231`, `transaction.py:37-64` | — | **documentation** of `CheckReadyForCommit("Commit at wrong place.")`, `CheckNotProcessingDataChanges`, depth-1 semantics | — |
| `exceptions.py:87-89` | — | `FP_TransactionError` definition | — |

Tests pinning Category B: `tests/test_custom_field_create_refusal.py:45,127-140`; `tests/test_b1t_action_handler_double.py:42-64,280-460,687`; `tests/operations/test_abort_session_live.py:48-49,242-266,276`; `tests/operations/test_issue243_closeproject_probe.py` (P2/P5/P7/P8/P9, esp. `:517-534,553-606,723-754,844-894,1029-1217`); `tests/test_transaction_honesty.py:63-99`; `tests/contract/test_lcm_contract.py:390`; `tests/conftest.py:1467,1492`. Category A pinned by `tests/test_headless_lcm_ui.py:71-95` (ConflictingSave raises; returns False when opted out) and `tests/contract/test_lcm_contract.py:456`. No test pins `FP_FileLockedError` behaviour.

## Answers

**1. Category A refusals: two, and neither is a flexicon-evaluated predicate.** `FLExProject.py:247-248` (re-raise of LCM's `LcmFileLockedException` as `FP_FileLockedError`) and `headless_ui.py:140-145` (`FP_ConflictingSaveError`, opt-out-able). There is **no** code anywhere in `flexicon/code/` that inspects whether a project is shared, whether ShareMyProjects/S/R is enabled, or that demands exclusive access before writing. `ConstChartMarkerOperations.py:245` is a refusal about intra-project shared state, not multi-user access.

**2. `usm.Save()` call sites in the library — two, plus one backup file (not live).**
- `flexicon/code/FLExProject.py:379-380` (`CloseProject`) — **not depth-guarded.** The nearby `HasOpenSessionTask()` check at :349 guards only the `EndNonUndoableTask()` call; `usm.Save()` at :380 runs unconditionally, by design (comments at :324-339 state a raise must never skip it).
- `flexicon/code/FLExProject.py:755-756` (`SaveChanges`) — **not depth-guarded.** Only `if not self.writeEnabled: raise FP_ReadOnlyError()` at :752-753.
- `flexicon/code/FLExProject.py.backup:276-277` — dead backup copy.
- (`usm.Refresh()` at `FLExProject.py:802-803` uses the same accessor, also write-enabled-guarded only.)

**3. Internal reachability of `FLExProject.SaveChanges()` — none.** No file under `flexicon/code/`, `flexicon/sync/`, or any other library package calls `SaveChanges()`. Every occurrence in `flexicon/code/` is docstring or comment text (`FLExProject.py:303, 673, 735-750, 763, 788, 797, 908`). `flexicon/sync/` never calls `SaveChanges()`, `usm.Save()`, `Transaction()`, or `UndoableOperation()` — its only matches are the word "block" in `validation.py:22,105` and "shared project" in its own test docstrings. All live callers are tests (`tests/operations/test_abort_session_live.py:264`, `tests/operations/test_issue243_closeproject_probe.py:555,725,844,1032,1057`) and docs/examples.

**A new guard inside `SaveChanges()` would therefore change no library call path** — only user code and the probe/live tests above, notably `test_abort_session_live.py:264-266` which asserts `"Commit at wrong place"` propagates from `SaveChanges()`, and `test_issue243_closeproject_probe.py:594-606` which explicitly asserts that raise is unchanged.
