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
- [x] **A1c** `FLExProject.OpenProject(..., ui=None)` passthrough to `FLExLCM.OpenProject`.
- [x] **A1d** Tests: 12-member unit coverage of `HeadlessLcmUI`; regression asserting
      `ui=None` still constructs `FwLcmUI`.
- [x] **A4** `FLExProject.RefreshFromDisk()` wrapping `IUndoStackManager.Refresh()`.
      Without it one foreign FLEx save wedges auto-save for the rest of the session
      (`UnitOfWorkService.cs:245`). Affects BOTH modes.
- [x] **A2a** Delete `_GetTransactionAPI` `RollbackToMark` discovery
      (`FLExProject.py:470-524`) — the API does not exist in liblcm.
- [x] **A2b** Correct the fictional three-candidate docstring at `FLExProject.py:474-482`.
- [x] **A2c** `Transaction()` honesty pass — see **D4** below (name retained;
      mode-dependent semantics stated plainly).
- [x] **A2d** Move the per-transaction WARNING to a single one-shot warning at
      `OpenProject` time.
- [x] **A2e** `docs/EXCEPTION_HANDLING.md`: under `undoable=False` the atomicity unit is
      the **session**; a mid-operation exception leaves prior mutations applied.
- [x] **CB** Contract-baseline extension (`tests/contract/snapshots/liblcm_baseline.json`)
      covering `UndoableUnitOfWorkHelper`, `NonUndoableUnitOfWorkHelper`,
      `IActionHandler`, `ILcmUI`. Must land **before** B1.
- [x] **MCP** `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md` — written contract FlexToolsMCP can
      build on: what `undoable=False` guarantees, what it does not, the shared-mode
      prohibition (D3), and the migration path to `undoable=True`.

**Checkpoint:** Track A green — COMPLETE. Landed on `main` (not pushed) as
`b3a5bb9` (impl, closes #236 #238), `17a8740` (contract baseline), `7404163` (docs).

---

## Checkpoint 2 — Track B core (`undoable=True` correctness)

Per **D3** this is the critical path for interactive shared-mode use, not follow-up.
Shape of B2 fixed by **D5** below (per-site, all 294).

### Checkpoint 2a — engine (this spurt)

- [ ] **B1** Rewrite `transaction.py` on `UndoableUnitOfWorkHelper`; delete
      `_transaction_depth` outright (kills #234 by construction). Use the liblcm nesting
      idiom verbatim: `if actionHandler.CurrentDepth > 0: task() else: Do(...)`.
      Closes #233, #234, #236-for-undoable. **174** `with self._TransactionCM(...)` call
      sites across the tree must keep working unchanged. Does **not** close #237 — that
      needs B2 + B2t.
- [ ] **B3** `Undo()`/`Redo()` on `cache.ActionHandlerAccessor`, gated on
      `CanUndo()`/`CanRedo()`. Delete the dead `if undo_stack is None` and `else`
      branches at `FLExProject.py:719-733` and `:765-779`. Close #235 as
      **in-process-only**, recording that scope caveat on the issue.
- [ ] **B1t** Offline tests: nesting join-vs-open, inner-CM raise leaves no residual
      depth, double-`BeginUndoTask` guard. Uses an action-handler double; **no live
      LCM write**.
- [ ] **B2g** Ratchet guard: AST mutator scan as a pytest with a frozen baseline, so the
      294 can only shrink and no 295th can be added unnoticed. Makes D5 enforceable.

### Checkpoint 2b..2n — the sweep (later spurts, batched by domain)

- [x] **B2s** Sweep inventory complete: `reviews/cycle1-explore-b2sweep.md` (294 methods).
- [ ] **B2** Bracket all 294 per **D5**. Batched by domain, one commit per batch, guard
      baseline ratcheted down each time: Lexicon 84, Grammar 59, Notebook 44,
      TextsWords 24, Discourse 21, Lists 14, code-root 13, System 11, Scripture 9,
      Shared 9, Reversal 6.
      Includes the 17 residual hand sites (8 catalog-chain private helpers, 6
      `FLExProject` methods, 3 undecorated `CatalogBackedMixin` publics) that no scheme
      covers mechanically.
- [ ] **B4** `flexicon.CAPABILITIES` frozenset, shipping the `per-operation-uow` token.
      Gated on B2 complete — contract §3 marks it PLANNED and the token must not appear
      before the capability is real.
- [ ] **B2t** End-to-end persistence test from #237: `undoable=True` -> `SetGloss` ->
      `CloseProject` -> reopen -> assert persisted. **Requires a live LCM write to a
      scratch project; needs_human gate. No agent may execute this.**

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

- **D5 — B2 bracket shape: PER-SITE, all 294. RESOLVED (cycle 3).** Reverses the
  provisional cycle-2 preference for a central bracket at the `@OperationsMethod`
  dispatch layer. Evidence: `reviews/cycle2-explore-dispatch-layer.md`.

  *Why the central bracket lost:*
  1. **P3 is dispositive.** 12/12 sampled methods across 12 domains are strictly
     validate-then-mutate, zero interleave — the exact discipline
     `BaseOperations.py:1784-1787` instructs and the codebase actually keeps. A
     dispatch-layer bracket pulls `_EnsureWriteEnabled`/`_Validate*` *inside* the UoW,
     so every rejected input opens an undo task, raises, and closes it. Under B1 that
     is not merely an empty named entry on a linguist's Ctrl+Z stack — with
     `UndoableUnitOfWorkHelper` it also fires a real `Rollback(0)`. 100% of the sample
     regresses, and it is fixable only by hoisting validators out of 294 method
     bodies, which is the per-site edit cost we were trying to avoid.
  2. **P4 label fidelity.** 50/174 (29%) existing sites use argument-derived labels
     (`f"Create entry '{form}'"`). A central `func.__name__` bracket degrades the FLEx
     undo menu to `LexEntryOperations.Create`. That menu is product surface a linguist
     reads; the existing 174 sites are the codebase's own evidence that per-site,
     argument-derived labelling is the house convention.
  3. **The hybrid is unbuildable as specified.** It needs a "first mutation" hook that
     does not exist in liblcm. We have already been burned once assuming an unverified
     API existed (`RollbackToMark`, #236). Not twice. The probe concedes that if the
     hook is unreachable the hybrid collapses to "central + ~50-67 hand edits".
  4. **P2 generators.** 48 decorated methods contain a top-level `yield`; a
     dispatch-layer `with` exits before the generator's first frame runs. Latent today
     (overlap with the 294 is 0) but it makes correctness depend on "nobody ever
     writes a `yield`-based writer" across 1144 decorated methods.
  5. **Residual is nonzero under every shape** — 17 hand sites minimum. Central buys
     91% mechanical coverage with the wrong semantics *and still* needs handwork.

  *Honest cost of the choice:* 294 edits instead of ~17. Accepted, because each is a
  mechanical two-line change (indent body, add `with`), it is batchable by domain, it
  introduces no new concept a future maintainer must learn, and it is `grep`-auditable
  per site — which a central bracket is not. **B2g** makes that auditability a CI
  ratchet rather than a promise.

  *Reversibility:* per-site preserves the option. A central net can be added on top
  later (it would find `CurrentDepth > 0` and join). The reverse — retrofitting
  per-site labels and validator hoists under a shipped central bracket — is not
  cheaply reversible. Choose the option that keeps options.

  *Not adopted from the probe:* its hybrid recommendation. Adopted instead: its own
  stated fallback, which it correctly calls "more honest, fully auditable by grep, and
  preserves label fidelity everywhere."
