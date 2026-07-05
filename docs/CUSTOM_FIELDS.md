# Custom Fields — Workflow and Transaction Safety

## TL;DR

**Do not create custom fields from scripts in Phase 1 transaction mode.** Use the
FLEx UI to create custom fields *before* you run any bootstrap script that
populates values via `SetValue`. If you bypass this guidance — for example by
calling raw `IFwMetaDataCacheManaged.AddCustomField` from Python — you can
silently corrupt the project on the next FLEx UI open.

## Why scripted creation is currently refused

`CustomFieldOperations.CreateField` raises `FP_TransactionError` when called
inside an open UnitOfWork. This is the LCM contract, not a wrapper limitation:

- A custom field is a **schema mutation**, not a data mutation. It registers a
  new field-id (flid) in the `MetaDataCacheAccessor` and emits a
  `CustomFieldAdded` PropChanged.
- LCM enforces that schema mutations cannot run inside an active data UoW.
  Attempting it raises `InvalidOperationException` at
  `UndoStack.CheckNotProcessingDataChanges` ("Nested tasks are not supported").
- In **Phase 1 transaction mode** (the default and currently only mode),
  `FLExProject.OpenProject` calls `MainCacheAccessor.BeginNonUndoableTask()`
  immediately and that envelope stays open until `CloseProject()`. There is no
  point in the lifetime of an open project where `AddCustomField` can succeed.

## The corruption mechanism (issue #21)

If you bypass `CreateField` and call raw LCM `AddCustomField` from inside an
open UoW, the following happens — silently, without error:

1. `mdc.AddCustomField(class, name, type, listClid)` returns a flid. The field
   exists in the **in-memory** MDC. `FindField(class, name)` immediately returns
   that flid; `IsMultiString(flid)` returns the right answer. Everything looks
   correct.
2. You proceed to call `SetValue(obj, name, value, ws)` on N objects. Each
   succeeds in memory.
3. `project.SaveChanges()` raises `InvalidOperationException: Commit at wrong
   place` at `UndoStack.CheckReadyForCommit`. If your script doesn't error-check
   the save, you may not notice.
4. On script exit, the underlying `.fwdata` write completes — but the schema
   addition is **not** persisted alongside it. The data writes referencing the
   new field name are persisted; the field definition is not.
5. On next FLEx UI open: **"Project contains a corrupted record. FieldWorks
   will have to close. Error Details: Fieldname '*Plural*' does not exist."**
   The user is forced to either (a) manually create the field in the FLEx UI
   with the *exact* same name/type/WS to reconnect to the orphan data, or
   (b) discard the entries.

This is the failure mode that produced issue #21. The session that caused it
created 1,392 senses with stranded `Plural` data references.

## Recommended workflow

### For bootstrap scripts that need a custom field

```text
1. Open the project in the FLEx UI.
2. Tools > Configure > Custom Fields > Add.
   Set name, owner class (e.g. LexSense), type (e.g. MultiString), WS (e.g. vernacular).
3. Click OK; save; close FLEx.
4. Run your bootstrap script. SetValue() will succeed against the persisted field.
```

### For test/CI scripts that need a fresh schema

Maintain a "template" FLEx project with the custom fields you need, already
created via the UI. Copy that template directory at test setup; never try to
add fields from inside the test.

## What the wrapper enforces

`CustomFieldOperations.CreateField` (in
`flexlibs2/code/System/CustomFieldOperations.py`) checks
`ActionHandlerAccessor.CurrentDepth > 0` before doing anything. In Phase 1
mode this is always true, so the call always raises:

```python
FP_TransactionError: CreateField cannot run inside an open UnitOfWork.
Custom field creation is a schema mutation that LCM forbids inside an active
task (raises InvalidOperationException at UndoStack.CheckNotProcessingDataChanges).
In Phase 1 transaction mode this UoW is opened at OpenProject() and stays open
until CloseProject(), so schema mutations are not possible via the wrapper.
Fix: create custom fields through the FLEx UI (Tools > Configure > Custom Fields)
before running bootstrap scripts that populate values.
Do NOT bypass this guard with raw IFwMetaDataCacheManaged.AddCustomField:
the field is created in memory only, SetValue writes data referencing a ghost
field, and the project corrupts on next FLEx UI open (issue #21).
See docs/CUSTOM_FIELDS.md.
```

## Future work

Programmatic custom field creation will likely become possible when **Phase 2
transaction mode** lands (see `FLExProject.UndoableOperation`). Phase 2 does
not open a global non-undoable envelope at `OpenProject` — each
`UndoableOperation` block opens and closes its own task — so there are gaps
between blocks where `AddCustomField` can run safely.

The recipe will be:

1. Open project in Phase 2 mode (`undoable=True`).
2. Before any `UndoableOperation` block, call `CreateField` (no active task →
   `CurrentDepth == 0` → guard passes → schema mutation runs in a fresh
   `NonUndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW`).
3. Then enter `UndoableOperation` blocks to populate data.

Tracking issues: #20, #21. See `docs/TRANSACTION_GUIDE.md` for transaction
mode background.

## See also

- Issue #20 — original `NotImplementedError` report
- Issue #21 — corruption-on-reopen postmortem
- `docs/TRANSACTION_GUIDE.md` — Phase 1 vs Phase 2 transaction modes
- `docs/internal/RESEARCH_NEEDED.md` — open questions on LCM transaction semantics
- `flexlibs2/code/System/CustomFieldOperations.py` — the guard
