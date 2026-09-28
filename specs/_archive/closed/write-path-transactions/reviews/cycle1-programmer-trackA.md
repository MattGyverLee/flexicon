# Cycle 1 — Programmer (Track A) report

## Landed

- **A1c** `FLExProject.OpenProject(self, projectName, writeEnabled=False, undoable=False, ui=None)`
  at `flexicon/code/FLExProject.py:163`. Passes `ui` through to
  `FLExLCM.OpenProject(projectName, ui)` (`:201`). Docstring (`:172-192`)
  documents the param and points headless callers at
  `flexicon.code.headless_ui.HeadlessLcmUI`. Default unchanged (verified:
  monkeypatch test shows `FwLcmUI` still constructed when `ui=None`).
- **A4** `FLExProject.RefreshFromDisk()` at `FLExProject.py:547-579`. Wraps
  `IUndoStackManager.Refresh()` via `self.ObjectRepository(IUndoStackManager)`,
  same accessor as `SaveChanges()` (`:520`) / `CloseProject()` (`:262`). Guards
  on `writeEnabled` (raises `FP_ReadOnlyError`), matching `SaveChanges()` —
  reasoned in the docstring: the wedge this fixes only occurs inside an open
  UnitOfWork, which only exists when write-enabled. Confirmed `Refresh()`
  signature (no args, void) by reading `liblcm/src/SIL.LCModel/InterfaceDeclarations.cs:1150`.
- **A2a/A2b** `_GetTransactionAPI` deleted outright (was `FLExProject.py:470-524`);
  `Transaction()` now constructs `_FLExTransaction(self, label, None, None)`
  directly (`:503`) — no discovery, no `RollbackToMark` reference anywhere.
  Confirmed absent from `liblcm/src/SIL.LCModel/Infrastructure/…` and
  `IActionHandler` by reading `ILcmUI.cs`/`InterfaceDeclarations.cs`.
- **A2c** `Transaction()` docstring rewritten (`FLExProject.py:452-505`):
  states plainly, up front, no rollback under `undoable=False`, atomicity
  unit is the session; deleted the fictional per-mark nesting Note. Name
  kept per D4. Same honesty pass on `UndoableOperation()`'s stale claim
  (`:625-634`, referenced `Transaction()` as an atomic fallback — false) and
  on `BaseOperations._TransactionCM` (`flexicon/code/BaseOperations.py:1767-1838`,
  docstring only, behavior/signature untouched). `transaction.py`'s class
  and `__enter__` docstrings corrected to match (no more "not yet
  discoverable" framing — it doesn't exist, period).
- **A2d** One-shot warning added at `OpenProject` (`FLExProject.py:236-249`,
  inside the `writeEnabled and not undoable` branch); per-call
  `logger.warning` in old `_GetTransactionAPI` is gone with the method; the
  per-call `logger.debug` at old `transaction.py:157-160` removed.
- **A2e** `docs/EXCEPTION_HANDLING.md`: new section "Atomicity Under
  `undoable=False`: the Session Is the Unit" (before "Testing Exception
  Handlers").
- **A1d** Two new test files, `tests/test_headless_lcm_ui.py` (21 tests) and
  `tests/test_transaction_honesty.py` (13 tests). Cover: all 12 `HeadlessLcmUI`
  members, `ConflictingSave()` raises and never returns `True`, no
  `.Invoke(`/`.BeginInvoke(` in source, `OpenProject` defaults to `FwLcmUI`
  (monkeypatched `LcmCache.CreateCacheFromExistingData`, no project opened),
  `FLExProject.OpenProject` signature accepts `ui=`, string-sweep asserting
  no `RollbackToMark` anywhere under `flexicon/code/`, `RefreshFromDisk`
  behavior, one-shot-warning presence, Transaction() honesty.

**Bug found and fixed in scope**: `HeadlessLcmUI` (`flexicon/code/headless_ui.py`)
was missing `RestoreLinkedFilesInProjectFolder` — confirmed against
`ILcmUI.cs`, a real 10-method/2-property interface. Without it the "12-member"
claim in A1b's docstring was false (9 methods implemented, not 10). Added the
non-destructive implementation (`:187-198`).

## Test results (actually run)

- `tests/test_headless_lcm_ui.py` + `tests/test_transaction_honesty.py` +
  `tests/operations/test_transaction_rollback.py`: **46/46 passed**.
- Full suite excluding `tests/contract/` (other agent's area):
  **1414 passed, 57 failed, 9 skipped** — identical 57 failures (verified via
  `git stash`/re-run on the pre-change tree: same 57, same names). All are
  pre-existing stale-path breakage from the flexlibs2→flexicon rename
  (e.g. `Path("flexlibs2/code/...")` relative paths that no longer resolve),
  unrelated to Track A. Zero regressions introduced.

## Not completed

None of the assigned task IDs (A1c, A4, A2a-A2e, A1d) were skipped.

## Files touched

`flexicon/code/FLExProject.py`, `flexicon/code/transaction.py`,
`flexicon/code/BaseOperations.py` (docstring only), `flexicon/code/headless_ui.py`
(one missing method), `docs/EXCEPTION_HANDLING.md`,
`tests/test_headless_lcm_ui.py` (new), `tests/test_transaction_honesty.py` (new).
`tests/contract/` and Operations classes untouched.
