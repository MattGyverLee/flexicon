# SPEC — write-path-transactions

**Repo:** flexicon, branch `main`
**Covers issues:** #233, #234, #235, #236, #237, #238
**Origin:** Write-path audit of flexicon 4.3.0 conducted 2026-08-13 while diagnosing why
MCP-driven writes silently produced no data.
**Status:** Draft — not yet dispatched to a crew cycle.
**Consumer constraint:** FlexToolsMCP is reverting to `undoable=False`. This spec is
written against that decision and prioritises accordingly.
**Do-not-list for this feature:** no live-LCM writes against a non-scratch project; no
change to the `undoable=False` default in this cycle; no git commits until Track A
passes verification.

## 1. Problem statement

flexicon hand-rolled a transaction layer (`flexicon/code/transaction.py`,
`flexicon/code/undoable_operation.py`, `FLExProject._GetTransactionAPI`,
`FLExProject._GetUndoRedoAPI`) that duplicates infrastructure liblcm already provides.
Every one of issues #233-#237 is a symptom of that single decision:

- #233 — `BeginUndoTask` invoked with one argument against a two-argument API.
- #234 — a hand-maintained `_transaction_depth` counter that leaks permanently when the
  inner context manager's `__enter__` raises.
- #235 — `Undo()`/`Redo()` reading `LcmCache.UndoStack`, a member that does not exist.
- #236 — rollback discovery targeting `RollbackToMark`, an API that exists nowhere in
  liblcm or FieldWorks.
- #237 — `undoable=True` opening no UnitOfWork envelope, so single-mutation setters and
  raw-LCM caller code are refused by LCM.

#238 is independent: `FLExLCM.OpenProject` hardcodes the WinForms `FwLcmUI` as the
`ILcmUI` handed to LCM, which in a headless process yields orphaned modal dialogs, a
deadlockable commit thread, and a save-conflict path that defaults to discarding the
caller's writes.

### 1.1 The reframing that drives this spec

With FlexToolsMCP on `undoable=False`, **four of the six issues are unreachable on the
live path**:

| Issue | Reachable under `undoable=False`? | Why |
|---|---|---|
| #233 | No | Fires only in the `elif undoable:` branch at `transaction.py:64-65`. |
| #234 | No (behaviourally) | The leaked counter only changes control flow via the `if undoable and depth > 0` branch at `transaction.py:57`. |
| #235 | No | `Undo()` raises `FP_TransactionError` at `FLExProject.py:665-669` before reaching the broken `UndoStack` read. Same guard on `Redo()`. |
| #237 | No | Definitionally scoped to `undoable=True`. |
| **#236** | **Yes** | `_GetTransactionAPI` returns `(None, None)` regardless of mode; every `with project.Transaction(...)` runs with no rollback in both modes. |
| **#238** | **Yes — and worse in this mode** | The session-long `NonUndoableUnitOfWork` is precisely the stack `RevertToSavedState` cannot revert cleanly. |

So the MCP decision narrows exposure to the two issues that can actually lose a user's
data, but it does **not** de-risk the write path, and it makes #238 more acute rather
than less: `undoable=False` puts the entire session in the non-undoable stack, which is
the branch liblcm annotates `// if there's a change here that conflicts we are dead`.

> **Revised 2026-08-14.** This table remains accurate for *single-process* use. It does
> not hold for interactive shared-mode use alongside an open FLEx, where `undoable=False`
> is not viable at all. See **D3**, which supersedes the framing here and reclassifies
> Track B as the critical path rather than follow-up work.

## 2. Verified LCM surface

Obtained by reflection over the installed `C:\Program Files\SIL\FieldWorks 9\SIL.LCModel.dll`
(liblcm 11.0.0). This is the evidence base for every recommendation below; it supersedes
the API-shape guesses embedded in the current code and docstrings.

```
UndoableUnitOfWorkHelper   (SIL.LCModel.Infrastructure)   IDisposable = True
    ctor(IActionHandler actionHandler, String undoText, String redoText)
    ctor(IActionHandler actionHandler, String message)
    P  RollBack : Boolean
    M  Do(String, String, IActionHandler, Action)
    M  DoUsingNewOrCurrentUOW(String, String, IActionHandler, Action)

NonUndoableUnitOfWorkHelper (SIL.LCModel.Infrastructure)  IDisposable = True
    ctor(IActionHandler actionHandler)
    P  RollBack : Boolean
    M  Do(IActionHandler, Action)
    M  DoUsingNewOrCurrentUOW(IActionHandler, Action)
    M  DoUsingNewOrCurrentUowOrSkip(IActionHandler, String, Action)

IActionHandler (SIL.LCModel.Core.KernelInterfaces)
    BeginUndoTask(String, String)        <- two args, confirmed at the interface
    BeginNonUndoableTask() / EndNonUndoableTask() / EndUndoTask()
    Rollback(Int32)  Mark()  DiscardToMark(Int32)  CollapseToMark(Int32, String, String)
    CanUndo()  CanRedo()  Undo()  Redo()
    P CurrentDepth : Int32   P UndoableActionCount : Int32

ILcmUI (SIL.LCModel)   -- 10 methods, 2 properties, no IDisposable
    ConflictingSave()  DisplayMessage(MessageType, String, String, String)
    ReportException(Exception, Boolean)  Retry(String, String)
    OfferToRestore(String, String)  ReportDuplicateGuids(String)
    DisplayCircularRefBreakerReport(String, String)  ChooseFilesToUse()
    RestoreLinkedFilesInProjectFolder()  CannotRestoreLinkedFilesToOriginalLocation()
    P LastActivityTime : DateTime   P SynchronizeInvoke : ISynchronizeInvoke

SilentLcmUI (SIL.LCModel)
    ctor(ISynchronizeInvoke synchronizeInvoke)     -- note: no IHelpTopicProvider
```

Three findings follow directly:

1. **`RollbackToMark` does not exist.** Confirmed absent from `IActionHandler`. The
   three-candidate discovery order documented at `FLExProject.py:474-482` describes a
   fictional API and must be corrected regardless of what else ships.
2. **liblcm already ships context-manager-shaped transaction helpers.** Both helpers are
   `IDisposable` with a `RollBack` property — the exact shape `transaction.py`
   reimplemented by hand and got wrong.
3. **`ILcmUI` is a 12-member surface.** A Python implementation is a bounded, few-hour
   task, and `SilentLcmUI` is not a drop-in (different ctor, and its `ConflictingSave()`
   returns `true` unconditionally, i.e. silent total discard).

## 3. Settled design decisions

### D1 — Rollback granularity is UnitOfWork granularity. This is a property, not a bug.

In `undoable=False`, `OpenProject` calls `MainCacheAccessor.BeginNonUndoableTask()` once
(`FLExProject.py:236-241`) and `CloseProject` calls `EndNonUndoableTask()`
(`FLExProject.py:255-257`). The whole session is therefore **one** UnitOfWork.

You cannot have both "unbracketed setters just work" and "per-operation rollback" in
this mode. They are mutually exclusive: the session-level envelope is exactly what makes
unbracketed mutation legal, and it is exactly what collapses the rollback unit to the
whole session. Nesting does not rescue this — `DoUsingNewOrCurrentUOW` reuses the
current UOW when one is open, so a nested helper has nothing separate to roll back.

**Decision:** keep the session-level envelope in `undoable=False` (it is what makes the
mode work, and FlexToolsMCP depends on it), and stop advertising per-operation rollback
in that mode. See A2.

### D2 — `undoable=True`, when fixed, uses per-operation brackets, not a session envelope.

#237 leaves this open. Resolve it as per-operation:

- A session-level undoable envelope would accumulate every UnitOfWork for the entire run
  in RAM holding live `ICmObject` references. On a 2,439-entry project that is a real
  memory profile, and it is the reason FieldWorks itself uses non-undoable UOW for bulk
  operations.
- Per-operation brackets are what make the `RollBack` flag meaningful at all.
- Per-operation matches the in-tree precedent (`UndoableUnitOfWorkHelper.Do`).

### D3 — `undoable=False` is incompatible with shared mode. This supersedes the MCP revert.

**Revised 2026-08-14 after reading `liblcm/src/SIL.LCModel/Infrastructure/Impl/`.** The
earlier position ("undoable=False is not safer, but keep it as default") understated the
problem. It is not merely less safe — for an interactive MCP running alongside an open
FLEx in shared mode it is unusable.

**Shared mode is designed around the undo stack.** `ChangeReconciler.cs:17-34` compares
"the (unsaved) changes in the current UOW" against another client's saved changes; it
walks `UowService.UndoStacks` and rewrites unsaved actions' before-states so "undoing
them will restore the state saved elsewhere." `MakeBundlePredateUnsavedBundles`
(`:678-698`) renumbers sequences so foreign work predates ours, explicitly so that "we
can Undo our own changes." Undo is not tolerated in shared mode; liblcm does real work
to keep it valid.

**The conflict test is narrow and object-granular.** `OkToReconcileChanges`
(`ChangeReconciler.cs:54-134`) returns false only on same-object collisions: both
deleted it, both modified it irreconcilably, one deleted what the other modified, or a
dangling reference results. It explicitly tolerates `DateModified` collisions
(`:164-168`) and owning-collection changes (`:176-177`) — the two things normal lexical
work generates most. Disjoint edits reconcile silently.

**The conflict window is unsaved changes, and `undoable=False` maximises it.**

```
UnitOfWorkService.cs:240   if (UndoOrRedoInProgress || CurrentProcessingState != ReadyForBeginTask)
                               return;                      // auto-save skipped
UnitOfWorkService.cs:304   m_activeUndoStack.CheckReadyForCommit("Commit at wrong place.");
```

`undoable=False` holds `BeginNonUndoableTask()` from `OpenProject` to `CloseProject`
(`FLExProject.py:236-241`, `:255-257`), so the FSM sits in `ProcessingDataChanges` for
the entire session. Auto-save therefore never fires, and an explicit `Save()` throws.
Nothing reaches disk until close. Consequently:

- The unsaved dirtball set grows monotonically across the whole session, so every FLEx
  save is tested against the session's entire accumulated footprint. On a multi-thousand
  entry sweep, intersection approaches certainty.
- On failure: `ConflictingSave()` -> headless dialog (#238) -> `RevertToSavedState()`,
  which cannot cleanly revert the non-undoable stack.
- Any crash loses the entire session.

Under `undoable=True` with D2's per-operation brackets, each operation returns the FSM to
`ReadyForBeginTask`, auto-save fires between operations (10s throttle, `:255`), and the
unsaved set stays at roughly one operation.

**Decision:** `undoable=True` + D2 per-operation brackets is the only configuration
compatible with interactive shared-mode use. Track B is therefore **not** optional
follow-up work — it is the prerequisite for the MCP's actual deployment mode. See §9.1.

Two corollaries:

- **Rollback must not be built on `Mark()`.** `UnitOfWorkService.cs:251` suppresses
  auto-save while any undo stack holds a mark, which would reintroduce the unbounded
  unsaved window. Use the `UndoableUnitOfWorkHelper.RollBack` mechanism from B1.
- **New requirement, not in any issue: headless `Refresh()`.**
  `UnitOfWorkService.cs:245` refuses to auto-save while `m_pendingReconciliation != null`
  — "don't auto-save until the user Refreshes." In a GUI a human clicks refresh.
  Headless, flexicon must call `IUndoStackManager.Refresh()` after a foreign change or a
  pending reconciliation wedges saving permanently for the rest of the session. Filed as
  A4.

## 4. Track A — the live path (ship first)

Everything in this track is reachable by FlexToolsMCP today.

### A1 — Injectable `ILcmUI` (#238)

**Priority: highest. This is the only issue in the cluster that can lose a user's data
today.**

- Add an optional `ui` parameter to `FLExLCM.OpenProject` and `FLExProject.OpenProject`,
  defaulting to the current `FwLcmUI(None, ThreadHelper())` for backward compatibility.
- Ship `flexicon/code/headless_ui.py` implementing `ILcmUI` in Python (pythonnet can
  implement .NET interfaces). Required semantics:
  - `ConflictingSave()` returns `False` — never the `RevertToSavedState()` branch — and
    raises a new `FP_ConflictingSaveError` so the conflict surfaces to the caller as an
    exception rather than as a dialog or a silent revert.
  - `DisplayMessage`, `ReportException`, `DisplayCircularRefBreakerReport`,
    `ReportDuplicateGuids` log at the appropriate level and return without blocking.
    They must never marshal through `ISynchronizeInvoke`.
  - `Retry` returns `False`; `OfferToRestore`, `ChooseFilesToUse`,
    `RestoreLinkedFilesInProjectFolder`,
    `CannotRestoreLinkedFilesToOriginalLocation` take the non-destructive branch and log.
  - `LastActivityTime` returns a real timestamp; `SynchronizeInvoke` returns `None`.
- Do **not** use `SilentLcmUI` as the implementation or the default. Its
  `ConflictingSave()` returns `true` unconditionally — silent total discard of unsaved
  changes with no message and no exception. It is strictly worse than the status quo.
- Note the latent `NullReferenceException`: `FwLcmUI` is constructed with
  `helpTopicProvider = None` (`FLExLCM.py:87-88`) and `DisplayMessage` dereferences
  `m_helpTopicProvider.HelpFile` for any non-empty `helpTopic`.

FlexToolsMCP should pass the headless UI explicitly once available. Until then it
remains exposed on every save conflict.

### A2 — Stop advertising rollback that does not exist (#236)

Take option 2 from the issue: stop advertising it. Option 1 (implement it for real) is
not available in `undoable=False` per D1, and building it only for `undoable=True`
belongs in Track B.

- Delete the `RollbackToMark` discovery in `_GetTransactionAPI` (`FLExProject.py:470-524`).
  It cannot succeed.
- Correct the docstring at `FLExProject.py:474-482`, which documents the fictional
  three-candidate discovery order as though it were live.
- `Transaction()` must stop reading as safe at the call site. Either rename it to
  something that does not promise atomicity (`OperationGroup` / `LabelledOperation`), or
  keep the name and have it state plainly in its docstring that it is a labelling and
  nesting construct with no rollback. Prefer the rename; the current name is the whole
  problem.
- Replace the once-per-transaction WARNING with a single warning at `OpenProject` time.
  Per-transaction logging trains callers to ignore it.
- Document in `docs/EXCEPTION_HANDLING.md` that under `undoable=False` the atomicity
  unit is the **session**: a mid-operation exception leaves every mutation up to that
  point applied.

### A3 — Expose the one real revert primitive that does exist

`IActionHandler.Rollback(Int32)` is present and is valid mid-task. Inside the
session-long non-undoable task, `Rollback(0)` should abort the entire session's
uncommitted changes. That is coarse, but it is a genuine capability and it is currently
unreachable from flexicon.

Add `FLExProject.AbortSession()` exposing it, documented as all-or-nothing for the
session and available in both modes. Gate on **O1** below before relying on it.

### A4 — Headless `Refresh()` after foreign changes (no issue filed)

Surfaced by the D3 investigation; not covered by #233-#238. `UnitOfWorkService.cs:245`
declines to auto-save while a reconciliation is pending, deferring to a user-initiated
refresh that never happens in a headless process. Expose `IUndoStackManager.Refresh()`
as `FLExProject.RefreshFromDisk()` and call it after a detected foreign change.

Without this, one foreign save from FLEx permanently wedges saving for the remainder of
the flexicon session — in **both** modes. File this as a new issue; it is a live-path
defect independent of the undoable question.

## 5. Track B — `undoable=True` correctness (after Track A)

Not on the MCP path once the revert lands, but the mode is public API and currently
cannot perform a single `SetGloss`.

### B1 — Rewrite `transaction.py` on the liblcm helper (#233, #234, #236-for-undoable)

These are one rewrite, not three patches. Delegate to `UndoableUnitOfWorkHelper` instead
of hand-rolling begin/end:

```python
def __enter__(self):
    ah = self._project.project.ActionHandlerAccessor
    self._nested = ah.CurrentDepth > 0          # ask LCM; do not track it yourself
    if not self._nested:
        self._helper = UndoableUnitOfWorkHelper(ah, self._label, self._label)
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    if self._helper is not None:
        self._helper.RollBack = exc_type is not None    # FW idiom: clear on success
        self._helper.Dispose()
    return False
```

- #233 cannot recur: the ctor takes both strings.
- #234 dies **by construction**: `_transaction_depth` is deleted outright. LCM's own
  `ActionHandlerAccessor.CurrentDepth` is authoritative, so there is no local state left
  to leak. This idiom is already in use at `CustomFieldOperations.py:300`.
- Rollback becomes real in `undoable=True`, fail-safe by default.

Approximately 180 `_TransactionCM` call sites across 59 files keep working unchanged —
the context-manager signature is preserved.

### B2 — Bracket the single-mutation setters (#237)

Per D2, wrap each in its own undo task. Known unbracketed mutators:
`LexSenseOperations.SetGloss`, `LexEntryOperations.SetLexemeForm`,
`LexEntryOperations.Delete`. Audit for the rest — `@OperationsMethod` is a dispatch
descriptor and adds no UoW wrapper, so any method that mutates without a
`_TransactionCM` is in scope. A sweep-pattern pass is warranted here.

### B3 — Fix `Undo()`/`Redo()` and close #235 as in-process-only

Two-line fix: read `cache.ActionHandlerAccessor` instead of the nonexistent
`LcmCache.UndoStack`, and gate on `CanUndo()`/`CanRedo()` before calling — `UndoStack.Undo()`
throws `InvalidOperationException("Can't undo")` on an empty stack rather than returning
a status, so a bare call cannot distinguish "nothing to undo" from a real failure. The
`if undo_stack is None` and `else` branches at `FLExProject.py:673-685` are dead code
and should be removed.

**Close #235 as in-process-only.** Cross-process undo is not achievable and no flexicon
change reaches it: LCM's stack is `Stack<UnitOfWork>` in RAM holding live `ICmObject`
references, nothing serialises undo records into `.fwdata`, and a fresh `LcmCache`
always starts at `UndoableActionCount == 0`. Record that scope on the issue when closing
so it is not reopened.

Cross-*session* reversal is a separate, still-open question and must not be conflated
with #235. It belongs at the wrapper layer, where flexicon already has the stub:
`flexicon/sync/engine.py:497-510` (`create_snapshot`, `NotImplementedError`, Phase 4) and
`:653` (`class Snapshot`). Out of scope here; do not close it as impossible.

## 6. Open questions requiring live verification

Reflection gives the shape of these APIs, not their bodies. Each must be confirmed
against a scratch project before code depends on it.

- **O1 — `UndoableUnitOfWorkHelper` disposal semantics.** Does `RollBack` default to
  `True`, and does `Dispose()` actually revert when it is set? This is read from the
  FieldWorks `using` idiom (`helper.RollBack = false;` as the last statement of a
  successful block), not from the method body. B1's entire rollback claim rests on it.
- **O2 — `Rollback(0)` inside a session-long non-undoable task.** `UndoStack.Rollback`
  throws `"Rollback not supported in the current state."` when called outside a task. A3
  assumes it is valid inside one. Confirm before exposing `AbortSession()`.
- **O3 — `DiscardToMark` semantics.** Whether it reverts data or merely discards undo
  records is unconfirmed. If it only discards records it is **not** a rollback primitive
  and must not be presented as one in any docstring. Current reading: it discards
  history, and `Rollback` is the only true revert.

## 7. Test plan

Track A:
- Headless `ILcmUI`: unit-test each of the 12 members in isolation; assert
  `ConflictingSave()` returns `False` and raises, and that no member touches
  `ISynchronizeInvoke`.
- Regression: assert `OpenProject` without `ui=` still constructs `FwLcmUI` (backward
  compatibility).
- Assert `_GetTransactionAPI` no longer references `RollbackToMark` (string-level test,
  mirroring the existing `tests/test_custom_field_create_refusal.py` pattern).

Track B:
- **The end-to-end test from #237, which would have caught the whole cluster:** open a
  scratch project with `undoable=True`, `SetGloss`, `CloseProject`, reopen, assert the
  value persisted.
- Force the inner CM to raise; assert no depth state survives (trivially true once
  `_transaction_depth` is deleted, but keep the test as a regression guard).
- Rollback: mutate inside a `_TransactionCM`, raise, assert the mutation reverted.
  Gated on O1.
- `Undo()` on an empty stack returns `False` rather than raising.

Extend `tests/contract/snapshots/liblcm_baseline.json` to cover
`UndoableUnitOfWorkHelper`, `NonUndoableUnitOfWorkHelper`, `IActionHandler`, and
`ILcmUI`. The baseline currently covers none of them, which is why the API-shape errors
in #233/#235/#236 survived a contract-test suite designed to catch exactly this.

## 8. Issue disposition

| Issue | Track | Resolution |
|---|---|---|
| #232 | — | Fixed at `9475768`. Unpushed; push to close. Family sweep continues under `specs/233-basetype-cast-sweep/`. |
| #238 | A1 | Injectable `ILcmUI` + Python headless implementation. |
| #236 | A2 | Stop advertising rollback; rename `Transaction()`; document session-level atomicity. |
| #233 | B1 | Dies with the `transaction.py` rewrite. |
| #234 | B1 | Dies by construction (`_transaction_depth` deleted). |
| #237 | B2 | Per-operation brackets on single-mutation setters. |
| #235 | B3 | `ActionHandlerAccessor` + `CanUndo()`; close as in-process-only with scope recorded. |

## 9. Sequencing

1. Push `9475768` (closes #232).
2. **A1** — injectable `ILcmUI`. Independent of everything else; highest data-loss risk.
3. **A4** — headless `Refresh()`. Small, affects both modes, currently wedges saving.
4. **A2** — rollback honesty. Small, and it stops callers building on a false guarantee
   while Track B is in flight.
5. **B1** — `transaction.py` rewrite, gated on O1.
6. **B2** — setter brackets + persistence test.
7. **B3** — `Undo()`/`Redo()`, close #235.
8. **A3** — `AbortSession()`, gated on O1/O2. Demoted below Track B: it is a
   session-granularity primitive whose value drops sharply once B1/B2 provide
   per-operation rollback.
9. Contract-baseline extension (§7) — any time after A1; before B1 so the rewrite is
   covered.
10. Flip the default to `undoable=True` (D3) once 6 is green.

### 9.1 Consequence for FlexToolsMCP

The revert to `undoable=False` is a safe short-term stabilisation **only for
single-process use** — no FLEx open, shared mode off. Under those conditions it remains
the correct choice and items 5-7 are not on its critical path.

For the interactive shared-mode case it is not viable, per D3: the session-long
non-undoable envelope suppresses all saving, grows the conflict window without bound,
and lands conflicts on the one stack that cannot be reverted. If interactive use
alongside an open FLEx is a requirement, **B1 and B2 are prerequisites, not follow-up**,
and the MCP should treat `undoable=False` as a temporary measure with shared mode
disabled rather than a destination.

This should be resolved with the FlexToolsMCP owners before Track B is scheduled, since
it determines whether Track B is optional hardening or the critical path.
