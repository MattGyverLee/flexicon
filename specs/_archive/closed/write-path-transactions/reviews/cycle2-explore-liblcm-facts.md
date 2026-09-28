# liblcm Source Facts for the FlexToolsMCP Contract

**Cycle:** 2
**Date:** 2026-08-14
**Source tree:** `D:\Github\_Projects\_LEX\liblcm`

> Persistence note: the Explore agent is read-only by design and returned these findings
> inline; written to this path by the orchestrator. Content verbatim, HTML entities
> normalised to plain `<` / `>`.

## F1. NESTING — CONFIRMED, and worse than "it throws"

Both call sites exist verbatim:

- `src\SIL.LCModel\Infrastructure\Impl\UndoStack.cs:194` — inside `BeginUndoTask`
  (declared line 187): `CheckNotProcessingDataChanges("Nested tasks are not supported.");`
- `UndoStack.cs:259` — inside `BeginNonUndoableTask` (declared line 252):
  `CheckNotProcessingDataChanges("Nested tasks are not supported.");`

A third occurrence with a different message context is at `UndoStack.cs:889`.

What happens on a second `BeginUndoTask` while one is open — `UndoStack.cs:209-216`:

```csharp
if (m_uowService.CurrentProcessingState == ...ProcessingDataChanges)
{
    Rollback(0);
    throw new InvalidOperationException(message);
}
```

So it is not merely rejected: the **already-open UoW is rolled back first** (all its
changes discarded, `UndoStack.cs:721-722`), the FSM is reset to `ReadyForBeginTask`
(`UndoStack.cs:724`), the write lock is released (`UndoStack.cs:716-717`), and then
`InvalidOperationException("Nested tasks are not supported.")` is thrown.
`BeginUndoTask` delegates to `ActiveUndoStack` first if `this != ActiveUndoStack`
(`UndoStack.cs:189-193`), so the check is always against the active stack.

## F2. CurrentDepth SEMANTICS — CONFIRMED

Verbatim, `UndoStack.cs:731-734`:

```csharp
public int CurrentDepth
{
    get { return m_uowService.CurrentProcessingState == UnitOfWorkService.BusinessTransactionState.ProcessingDataChanges ? 1 : 0; }
}
```

Only two possible values: **1 or 0** — never 2+. Doc comment `UndoStack.cs:730`:
"1 if in undo task, 0 otherwise". `BeginNonUndoableTask` sets exactly that state at
`UndoStack.cs:262`; `BeginUndoTask` sets the identical state at `UndoStack.cs:198`.

**Consequence: `CurrentDepth` cannot distinguish an undoable from a non-undoable task**,
and it is a state read on the *service*, not the stack.

## F3. THE JOIN IDIOM — canonical helper EXISTS

- `UndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW(string undoText, string redoText, IActionHandler actionHandler, Action task)`
  — `src\SIL.LCModel\Infrastructure\UndoableUnitOfWorkHelper.cs:91-98`. Body is literally
  the hand-rolled idiom: `if (actionHandler.CurrentDepth > 0) task(); else Do(undoText, redoText, actionHandler, task);`
  (lines 94-97).
- `UndoableUnitOfWorkHelper.Do(...)` — `UndoableUnitOfWorkHelper.cs:59-66`. Always begins
  a new task (ctor line 34); sets `RollBack = false` on success (line 64). Overload
  taking `ICmObject` at line 76.
- `NonUndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW(IActionHandler, Action)` —
  `NonUndoableUnitOfWorkHelper.cs:78-85`. Tests the service state directly rather than
  `CurrentDepth`: `if (uowService.CurrentProcessingState == ...ProcessingDataChanges) task(); else Do(actionHandler, task);`
  (lines 81-84).
- `NonUndoableUnitOfWorkHelper.Do(IActionHandler, Action)` — line 129; generic `Do<T>` —
  line 148.
- Also `DoUsingNewOrCurrentUowOrSkip` (line 94) and `DoSomehow` (line 111), which
  additionally handle the PropChanged phase (deferring via `DoAtEndOfPropChanged`,
  line 58/121).

**Canonical "join if already inside" helper: `DoUsingNewOrCurrentUOW`** (both flavours).
Callers do not hand-roll. Real callers: `src\SIL.LCModel\DomainImpl\OverridesLing_Lex.cs:300`,
`:4187`, `:5414`, `src\SIL.LCModel\LcmCache.cs:584`,
`src\SIL.LCModel\DomainImpl\ScrImportSet.cs:1194`.

## F4. SAVE CADENCE

Trigger: a `System.Timers.Timer` with `Interval = 1000` ms, `Elapsed += SaveOnIdle`,
started in the ctor — `src\SIL.LCModel\Infrastructure\Impl\UnitOfWorkService.cs:174-177`.

`SaveOnIdle` (`UnitOfWorkService.cs:226-263`) returns without saving if any of: already
in `SaveInternal` (231); disposed (234); `m_ui == null` (236);
**`UndoOrRedoInProgress || CurrentProcessingState != ReadyForBeginTask` (240)**;
repository disposed (243); pending reconciliation (245); any stack has
`TopMarkHandle != 0` (251); **less than 10 s since `m_lastSave` (255)**; **less than 2 s
since `m_ui.LastActivityTime`, unless `m_lastSave` is more than 5 minutes old (258)**.
Otherwise calls `SaveInternal()` (261).

**Ending a UoW does NOT guarantee a disk write.** `EndUndoTaskCommon`
(`UndoStack.cs:289-360`) contains no save call; it only sets state to `ReadyForBeginTask`
(line 354). The write happens only when the next timer tick passes all gates above.

`IUndoStackManager.Save()` (interface `src\SIL.LCModel\InterfaceDeclarations.cs:1105`,
method 1132 — "Save everything... Does NOT clear undo stacks") is implemented at
`UnitOfWorkService.cs:287-291`: `lock (this) SaveInternal();`. It **bypasses every
throttle** (10 s, 2 s activity, mark check) and goes straight to `SaveInternal` (293),
which still requires `ReadyForBeginTask` via `CheckReadyForCommit("Commit at wrong place.")`
(line 304) — and that check **rolls back** if the state is wrong (`UndoStack.cs:239-246`).
`SaveInternal` sets `m_lastSave` (305), raises `OnSave` (324), and calls
`m_dataStorer.Commit(...)` (341).

By contrast `UndoStack.Commit()` (`UndoStack.cs:744-754`) calls `m_uowService.Save()`
**and then `Clear()`** — it discards the undo stack. Real callers of the plain save:
`src\SIL.LCModel\DomainServices\BackupRestore\ProjectBackupService.cs:60` and
`src\SIL.LCModel\DomainServices\ProjectLockingService.cs:40`.

## F5. ROLLBACK REALITY

(a) `IActionHandler` is **not defined in this repo** — it lives in the external
`SIL.LCModel.Core` package (`grep "interface IActionHandler"` over `src/` returns only
`IActionHandlerExtensions` at `src\SIL.LCModel\Application\IActionHandlerExtensions.cs:25`).
Source-level: NOT FOUND IN SOURCE. Binary evidence only: the metadata string heap of
`~\.nuget\packages\sil.lcmodel.core\11.0.0-beta0150\lib\net462\SIL.LCModel.Core.dll`
contains `Rollback`, `CollapseToMark`, `CurrentDepth`, `BeginUndoTask` and **no**
`RollbackToMark`. No `RollbackToMark`/`RollBackToMark` occurs anywhere under `liblcm\src`.

(b) CONFIRMED. `UnitOfWorkHelper` ctor sets `RollBack = true` —
`src\SIL.LCModel\Infrastructure\UnitOfWorkHelper.cs:31`. `Dispose(bool)` at lines 115-116:
`if (RollBack) RollBackChanges();` else `EndUndoTask()` (117-118). `RollBackChanges()` at
lines 135-138 is exactly `m_actionHandler.Rollback(0);`. Note the finalizer (line 43)
also calls `Dispose(false)`, which does **not** roll back (guarded by `if (disposing)`,
line 113).

(c) CONFIRMED. `Rollback(int nDepth)` — `UndoStack.cs:705`. `nDepth` is documented
"[Not used.]" (line 700) and is only forwarded when delegating to the active stack
(line 709); it is never otherwise read. Requires `ProcessingDataChanges` else
`throw new InvalidOperationException("Rollback not supported in the current state.")`
(lines 712-713). Exits the write lock (716-717), rolls back the bundle (721), clears
`m_actionsToDoAtEndOfPropChanged` (723), and sets
`CurrentProcessingState = ReadyForBeginTask` (724).

## F6. SCHEMA MUTATION — CLAIM REFUTED

There is **no guard**. `LcmMetaDataCache.AddCustomField(string, string, CellarPropertyType, int)`
— `src\SIL.LCModel\Infrastructure\Impl\LcmMetaDataCache.cs:920-965` — validates class
name (922), empty field name (925), name collision (929-930), assures uniqueness (934),
allocates a flid (937-948), calls `AddField` (953), and returns. It never touches
`UnitOfWorkService`, `CurrentProcessingState`, or `CheckNotProcessingDataChanges`. Grep
for `uow|UnitOfWork|ProcessingDataChanges` across the whole of `LcmMetaDataCache.cs`
returns **zero hits**. The other overloads (`:1059`, `:1068`, `:1132`) and the decorator
(`src\SIL.LCModel\Infrastructure\MetaDataCacheDecoratorBase.cs:497`, `:557`) just
delegate. `CheckNotProcessingDataChanges` is `private` to `UndoStack`
(`UndoStack.cs:209`) and is called only from `BeginUndoTask` (194),
`BeginNonUndoableTask` (259), the `CollapseToMark` path (814) and line 889 — never from
metadata code.

Both usages exist in liblcm's own tests:

- **Inside** an open undoable UoW: `tests\SIL.LCModel.Tests\DomainImpl\LexEntryTests.cs:1075`
  (`MakeCustomProperty`), reached from `MakeEntryWithAllPropsSet` (`:928`), which is
  invoked inside `UndoableUnitOfWorkHelper.Do("doit", "undoit", Cache.ActionHandlerAccessor, ...)`
  at `LexEntryTests.cs:825-828`. It then does `m_sda.SetBoolean(...)` on the new flid
  (`:1078`) and the test asserts the value survives (`:924`). So schema mutation inside a
  data UoW is exercised and **passes** in liblcm's own suite.
- **Outside** any UoW: `tests\SIL.LCModel.Tests\Application\Impl\IDomainDataByFlidTests.cs:51-57`,
  in `[OneTimeSetUp] FixtureSetup()`.

**Correct programmatic sequence in source:** the production path is
`FieldDescription.UpdateCustomField()` — `src\SIL.LCModel\FieldDescription.cs:336` —
which for a new field calls `mdc.AddCustomField(...)` (`:406`), then
`mdc.UpdateCustomField(...)` (`:407`), then for value types marks every instance dirty
via `uowService.RegisterObjectAsModified(obj)` (`:411-413`) so the property is written
out for all objects. That `RegisterObjectAsModified` step is the piece raw
`AddCustomField` skips, and it requires an active UoW context. `FieldDescription.cs`
itself contains **no** `UndoableUnitOfWorkHelper`/`NonUndoableUnitOfWorkHelper` call —
the UoW is expected to be supplied by the caller (which lives in FieldWorks, not in this
repo: NOT FOUND IN SOURCE for the FLEx-side caller). Persistence of the schema itself
happens via `BackendProvider` (`src\SIL.LCModel\Infrastructure\Impl\BackendProvider.cs:799`,
`:929` calling `AddCustomFields`) at commit time.

**Bearing on the flexicon guard** at `flexicon\code\System\CustomFieldOperations.py:300-318`:
its stated rationale — "raises InvalidOperationException at
UndoStack.CheckNotProcessingDataChanges" (lines 288-289, 305-306) — is **not supported by
liblcm source**; liblcm's own tests do exactly that successfully. The *real* hazard the
guard describes (in-memory-only field, `RegisterObjectAsModified` never run, ghost flid)
is supported by `FieldDescription.cs:406-413` versus the bare
`LcmMetaDataCache.cs:920-965`.
