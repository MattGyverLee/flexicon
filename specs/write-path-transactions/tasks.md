# TASKS — write-path-transactions

Derived from `spec.md` §9 (Sequencing). Authoritative order; do not reorder without
recording a decision in `spec.md`.

Issues covered: #233 #234 #235 #236 #237 #238 + A4 (unfiled).

---

## Checkpoint 1 — Track A complete (live path)

Everything here is reachable by FlexToolsMCP today under `undoable=False`.

- [x] **A1a** `FLExLCM.OpenProject(projectName, ui=None)`, defaults to `FwLcmUI`.
- [x] **A1b** `flexicon/code/headless_ui.py` — `HeadlessLcmUI(ILcmUI)` +
      `FP_ConflictingSaveError`. Verified live via pythonnet (real .NET type,
      `isinstance(ui, ILcmUI)` True, all 10 methods + 2 properties exercised).
- [ ] **A1c** `FLExProject.OpenProject(..., ui=None)` passthrough to `FLExLCM.OpenProject`.
- [ ] **A1d** Tests: 12-member unit coverage of `HeadlessLcmUI`; regression asserting
      `ui=None` still constructs `FwLcmUI`.
- [ ] **A4** `FLExProject.RefreshFromDisk()` wrapping `IUndoStackManager.Refresh()`.
      Without it one foreign FLEx save wedges auto-save for the rest of the session
      (`UnitOfWorkService.cs:245`). Affects BOTH modes.
- [ ] **A2a** Delete `_GetTransactionAPI` `RollbackToMark` discovery
      (`FLExProject.py:470-524`) — the API does not exist in liblcm.
- [ ] **A2b** Correct the fictional three-candidate docstring at `FLExProject.py:474-482`.
- [ ] **A2c** `Transaction()` honesty pass — see **D4** below (name retained;
      mode-dependent semantics stated plainly).
- [ ] **A2d** Move the per-transaction WARNING to a single one-shot warning at
      `OpenProject` time.
- [ ] **A2e** `docs/EXCEPTION_HANDLING.md`: under `undoable=False` the atomicity unit is
      the **session**; a mid-operation exception leaves prior mutations applied.
- [ ] **CB** Contract-baseline extension (`tests/contract/snapshots/liblcm_baseline.json`)
      covering `UndoableUnitOfWorkHelper`, `NonUndoableUnitOfWorkHelper`,
      `IActionHandler`, `ILcmUI`. Must land **before** B1.
- [ ] **MCP** `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md` — written contract FlexToolsMCP can
      build on: what `undoable=False` guarantees, what it does not, the shared-mode
      prohibition (D3), and the migration path to `undoable=True`.

**Checkpoint:** Track A green — no live-LCM writes, no commits until verification passes.

---

## Checkpoint 2 — Track B core (`undoable=True` correctness)

Per **D3** this is the critical path for interactive shared-mode use, not follow-up.

- [ ] **B1** Rewrite `transaction.py` on `UndoableUnitOfWorkHelper`; delete
      `_transaction_depth` outright (kills #234 by construction). Use the liblcm nesting
      idiom verbatim: `if actionHandler.CurrentDepth > 0: task() else: Do(...)`.
      Closes #233, #234, #236-for-undoable. ~180 `_TransactionCM` call sites across 59
      files must keep working unchanged.
- [ ] **B1t** Tests: inner-CM raise leaves no depth state; rollback reverts a mutation.
- [ ] **B2s** Sweep: full inventory of unbracketed single-mutation mutators.
      Known: `LexSenseOperations.SetGloss`, `LexEntryOperations.SetLexemeForm`,
      `LexEntryOperations.Delete`. `@OperationsMethod` adds no UoW wrapper.
- [ ] **B2** Bracket each one per D2 (per-operation, not session envelope).
- [ ] **B2t** End-to-end persistence test from #237: `undoable=True` -> `SetGloss` ->
      `CloseProject` -> reopen -> assert persisted. **Requires a scratch project;
      needs_human gate.**

**Checkpoint:** Track B core green.

---

## Checkpoint 3 — Close-out

- [ ] **B3** `Undo()`/`Redo()` on `cache.ActionHandlerAccessor`, gated on
      `CanUndo()`/`CanRedo()`. Remove dead branches at `FLExProject.py:673-685` and
      `:718-731`. Close #235 as **in-process-only**, recording that scope on the issue.
- [ ] **A3** `FLExProject.AbortSession()` -> `IActionHandler.Rollback(0)`. Demoted below
      Track B. Must document the **O2 catch**: `Rollback` leaves the FSM in
      `ReadyForBeginTask`, so in `undoable=False` it terminates the session envelope and
      must either reopen `BeginNonUndoableTask()` or be documented as terminal.
- [ ] **DEF** Flip the default to `undoable=True` (D3). Gated on Checkpoint 2 green.
      **needs_human** — public API default change.

---

## Resolved open questions

- **O1 RESOLVED** (`UnitOfWorkHelper.cs`): ctor sets `RollBack=true` (:31); `Dispose`
  calls `RollBackChanges()` when set (:115-116), delegating to
  `m_actionHandler.Rollback(0)` (:137). `RollBack` is `{private get; set;}` — write-only
  from outside, so never read it back. B1's rollback claim holds.
- **O2 RESOLVED WITH CATCH** (`UndoStack.Rollback(int)`): ignores `nDepth`, requires
  `CurrentProcessingState == ProcessingDataChanges` (else throws), rolls back
  `m_currentBundle`, leaves the FSM in `ReadyForBeginTask`. See A3.
- **O3 STILL OPEN** (`DiscardToMark`): discards undo records vs reverts data —
  unverified. **Do not build on it.** Current reading: it discards history only, and
  `Rollback` is the sole true revert.

## Decisions added after spec.md

- **D4 — `Transaction()` keeps its name.** `spec.md` A2 preferred a rename
  (`OperationGroup`). That preference predates D3. Once B1 lands,
  `Transaction()` becomes genuinely transactional under `undoable=True` — the mode D3
  designates as the destination — so renaming it away would make the name wrong exactly
  where it is right. Take the alternative A2 explicitly permits: keep the name, and state
  mode-dependent semantics plainly in the docstring plus a one-shot `OpenProject`
  warning when `writeEnabled and not undoable`. Revisit only if QC/domain dissent.
