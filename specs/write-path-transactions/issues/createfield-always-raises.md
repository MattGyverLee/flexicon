# `CustomFieldOperations.CreateField` always raises `FP_TransactionError` — custom field creation is impossible via the wrapper in v4.3.0

**Suggested labels:** `bug`, `write-path`, `transactions`, `custom-fields`, `documentation`

> **Revision note (cycle 2):** this draft was originally marked CONFIRMED, but a
> subsequent liblcm source investigation (`reviews/cycle2-explore-liblcm-facts.md`,
> section F6) **refuted one of its supporting premises** — see "Correction #2"
> below. The core defect (CreateField always raises) is unaffected and has been
> re-verified independently, directly against `flexicon/code/System/CustomFieldOperations.py`
> in this pass. This revision removes the refuted premise, adds the corrected
> rationale as a second, separate defect, and adds a "Known correct implementation
> path" section so a future fix isn't starting from zero.

## Summary

`CustomFieldOperations.CreateField` (`flexicon/code/System/CustomFieldOperations.py:280-326`)
raises `FP_TransactionError` on **both** of its possible code paths. There is
no way to reach a successful return. This holds under the current default
session-wide transaction envelope (Phase 1, `undoable=False`), and — this is
the part that needs to be called out clearly — it will **still** hold after
a hypothetical migration to per-operation Units of Work (Phase 2/"Track B"),
because the second raise is unimplemented work, not a guard condition.

Separately, the in-code comment that explains *why* the guard at `:301`
exists (`:288-289`, `:305-306`) states a rationale that is not supported by
liblcm source — see Correction #2. That is a second, distinct defect (a
misleading comment/error message), not a challenge to the guard's existence
or to the always-raises defect above.

## Verified from source

All five links below were checked directly against the files named, not
assumed from the defect report. Re-confirmed in this revision pass by
re-reading `flexicon/code/System/CustomFieldOperations.py:270-326` directly.

1. **`CustomFieldOperations.py:300-301`** — the depth guard.
   ```python
   action_handler = self.project.project.ActionHandlerAccessor
   if getattr(action_handler, "CurrentDepth", 0) > 0:
       raise FP_TransactionError(...)
   ```
   Confirmed as written: reads `ActionHandlerAccessor.CurrentDepth` and
   raises `FP_TransactionError` if it is greater than 0.

2. **`liblcm/src/SIL.LCModel/Infrastructure/Impl/UndoStack.cs:727-734`**
   — `CurrentDepth` definition:
   ```csharp
   /// <summary>
   /// Gets the current depth of the nested BeginUndoTask() calls.
   ///</summary>
   /// <returns>1 if in undo task, 0 otherwise</returns>
   public int CurrentDepth
   {
       get { return m_uowService.CurrentProcessingState == UnitOfWorkService.BusinessTransactionState.ProcessingDataChanges ? 1 : 0; }
   }
   ```
   Confirmed: returns 1 iff `CurrentProcessingState ==
   BusinessTransactionState.ProcessingDataChanges`, 0 otherwise. No other
   state maps to 1. (Note also per F2 of the liblcm facts review:
   `CurrentDepth` cannot distinguish an undoable task from a non-undoable
   one — both set the identical state — but that distinction is not needed
   for the argument here.)

3. **`liblcm/src/SIL.LCModel/Infrastructure/Impl/UndoStack.cs:252-265`**
   — `BeginNonUndoableTask()`:
   ```csharp
   public void BeginNonUndoableTask()
   {
       if (this != m_uowService.ActiveUndoStack)
       {
           m_uowService.ActiveUndoStack.BeginNonUndoableTask();
           return;
       }
       CheckNotProcessingDataChanges("Nested tasks are not supported.");
       CheckNotBroadcastingPropChanges("Can't start new task, while broadcasting PropChanges.");
       CheckNotInUndoRedo();
       m_uowService.CurrentProcessingState = UnitOfWorkService.BusinessTransactionState.ProcessingDataChanges;
       m_uowService.m_lock.EnterWriteLock();
       m_currentBundle = new NonUndoableUnitOfWork(m_uowService);
   }
   ```
   Confirmed at line 262 (matches the claimed line number exactly):
   `m_uowService.CurrentProcessingState =
   UnitOfWorkService.BusinessTransactionState.ProcessingDataChanges;`.
   This is exactly the state `CurrentDepth` (link 2) tests for, so after
   `BeginNonUndoableTask()` returns, `CurrentDepth == 1` until a matching
   `EndNonUndoableTask()`/`Rollback()`/`Commit()` changes the state back to
   `ReadyForBeginTask`.

4. **`flexicon/code/FLExProject.py:256-279`** (`OpenProject`, Phase 1 branch
   — `writeEnabled and not undoable`, which is also the **default** since
   `undoable=False` is the default constructor arg):
   ```python
   if self.writeEnabled and not self._undoable:
       ...
       # Phase 1 behavior: whole session is non-undoable (rollback transactions only)
       try:
           # This must be called before calling any methods that change
           # the project.
           self.project.MainCacheAccessor.BeginNonUndoableTask()
       except System.InvalidOperationException:
           raise FP_ProjectError("BeginNonUndoableTask() failed.")
   ```
   and the matching close, `flexicon/code/FLExProject.py:285-295`
   (`CloseProject`):
   ```python
   if hasattr(self, "project"):
       if self.writeEnabled:
           if not self._undoable:
               # Phase 1: This must be called to mirror the call to BeginNonUndoableTask().
               self.project.MainCacheAccessor.EndNonUndoableTask()
   ```
   Confirmed: `OpenProject()` opens the non-undoable envelope immediately
   and unconditionally (in the default/Phase 1 mode) and the only place it
   is closed is `CloseProject()`. There is no intervening point in the
   object's lifetime where the envelope is closed.

   **Conclusion for links 1-4:** under the default session (`undoable=False`,
   `writeEnabled=True` — the only mode in which `CreateField` would be
   reachable at all, since read-only projects can't create fields),
   `CurrentDepth` is 1 for the entire `OpenProject()`...`CloseProject()`
   lifetime. The guard at `CustomFieldOperations.py:301` therefore **always**
   fires. Verified, not refuted. (What *is* refuted is a different claim —
   the stated *reason* the guard is safe to rely on. See Correction #2.)

5. **`CustomFieldOperations.py:320-326`** — the second, unconditional raise:
   ```python
   # Unreachable in Phase 1 mode; placeholder for Phase 2 work.
   raise FP_TransactionError(
       "CreateField is not yet implemented for the no-UoW path. "
       "Pending Phase 2 transaction mode (see FLExProject.UndoableOperation). "
       "Until then, create custom fields through the FLEx UI: "
       "Tools > Configure > Custom Fields. See docs/CUSTOM_FIELDS.md."
   )
   ```
   Confirmed: if execution ever reaches past the `:301` guard (i.e.
   `CurrentDepth == 0`), it raises unconditionally with its own
   `FP_TransactionError`, whose message states outright that the
   "no-UoW path" is **not yet implemented**. There is no `AddCustomField`
   call, no schema-mutation logic, anywhere in this method. It is a stub.

**All five links hold. The core defect is CONFIRMED as described, and
re-verified independently in this revision pass**: `CreateField` cannot
currently succeed under any reachable project state in v4.3.0.

## Correction #2 (this revision): the guard's stated rationale is not supported by liblcm source

The in-code comment and raised error message at
`CustomFieldOperations.py:288-289` and `:305-306` justify the `:301` guard
by claiming that schema mutation inside an open data UoW "raises
InvalidOperationException at UndoStack.CheckNotProcessingDataChanges".
Per `reviews/cycle2-explore-liblcm-facts.md` section F6, **this specific
claim is false**:

- `LcmMetaDataCache.AddCustomField(string, string, CellarPropertyType, int)`
  (`liblcm/src/SIL.LCModel/Infrastructure/Impl/LcmMetaDataCache.cs:920-965`)
  never touches `UnitOfWorkService`, `CurrentProcessingState`, or
  `CheckNotProcessingDataChanges`. A grep for
  `uow|UnitOfWork|ProcessingDataChanges` across the whole file returns
  **zero hits**.
- `CheckNotProcessingDataChanges` is `private` to `UndoStack`
  (`UndoStack.cs:209`) and is called only from `BeginUndoTask` (194),
  `BeginNonUndoableTask` (259), the `CollapseToMark` path (814), and line
  889 — never from any metadata/schema code.
- liblcm's own test suite performs schema mutation **inside** an open
  undoable UoW and it passes:
  `tests/SIL.LCModel.Tests/DomainImpl/LexEntryTests.cs:825-828`
  (`UndoableUnitOfWorkHelper.Do("doit", "undoit", Cache.ActionHandlerAccessor, ...)`)
  → `:928` (`MakeEntryWithAllPropsSet`) → `:1075` (`MakeCustomProperty`),
  then `:1078` sets a value on the new flid and `:924` asserts the value
  survives.
- Schema mutation **outside** any UoW also occurs at
  `tests/SIL.LCModel.Tests/Application/Impl/IDomainDataByFlidTests.cs:51-57`
  (`[OneTimeSetUp] FixtureSetup()`).

**Independently re-checked against `flexicon` source in this revision
pass**: `flexicon/code/System/CustomFieldOperations.py:288-289` and
`:305-306` do state the refuted rationale verbatim ("raises
InvalidOperationException at UndoStack.CheckNotProcessingDataChanges"),
confirming this is a real, present-day defect in the comment/error text,
not a stale claim from an earlier draft.

**This is presented as a second, distinct defect — not as grounds to
remove the guard.** Whether the `:301` guard should still exist is a
separate question from whether its *stated reason* is correct, and the
two must not be conflated when this is fixed:

- **The stated reason is wrong.** `AddCustomField` itself does not care
  about UoW state and does not raise `InvalidOperationException` for
  running inside one.
- **The guard may still be justified — by a different hazard.** The real
  risk the comment gestures at is the "ghost flid" problem: calling bare
  `LcmMetaDataCache.AddCustomField` skips `RegisterObjectAsModified`
  (see "Known correct implementation path" below), so the new field can
  end up in-memory-only from the UoW/commit machinery's point of view.
  `SetValue` calls against that field then reference a flid that was
  never registered as part of any object's modified set, and depending on
  commit/save timing this can produce the ghost-field/corruption-on-reopen
  scenario referenced by issue #21. Nothing in this revision establishes
  that removing the guard is safe; it only establishes that the guard's
  *written justification* cites the wrong mechanism.
- Whoever ultimately implements `CreateField` (Correction #1 below) needs
  to re-derive the actual constraint (probably something like "must run
  inside a UoW that will call `RegisterObjectAsModified` for affected
  instances, e.g. via `FieldDescription.UpdateCustomField`, not raw
  `AddCustomField`") rather than reusing the current comment's reasoning.

## Known correct implementation path (new in this revision)

For whoever implements the currently-stubbed schema mutation, liblcm
already contains a production-quality reference sequence — it is not
necessary to reverse-engineer one:

- `FieldDescription.UpdateCustomField()` —
  `liblcm/src/SIL.LCModel/FieldDescription.cs:336` — is the method liblcm's
  own production code uses to add or update a custom field. For a *new*
  field (the `!IsInstalled` branch) it:
  - calls `mdc.AddCustomField(sClass, m_name, ft, m_dstCls, m_helpString, m_wsSelector, m_listRootId)`
    (`FieldDescription.cs:406`),
  - then `mdc.UpdateCustomField(m_id, m_helpString, m_wsSelector, m_userlabel)`
    (`:407`),
  - then, if the field is a value type, iterates `Objects` and calls
    `uowService.RegisterObjectAsModified(obj)` for each one (`:411-413`) —
    this is the step that raw `AddCustomField` skips and that closes the
    ghost-flid gap described above.
- `FieldDescription.cs` itself contains **no**
  `UndoableUnitOfWorkHelper`/`NonUndoableUnitOfWorkHelper` call — the UoW
  is expected to be supplied by the *caller*. The FLEx-side caller that
  normally provides this UoW is **not in the liblcm repo** (NOT FOUND IN
  SOURCE); flexicon's implementation will need to supply its own, most
  plausibly via `NonUndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW` per
  the existing sketch in `docs/CUSTOM_FIELDS.md` "Future work", but that
  sketch has not been verified against `FieldDescription`'s actual
  sequence and should be reconciled with it, not implemented independently.
- Schema persistence to disk happens via `BackendProvider`
  (`liblcm/src/SIL.LCModel/Infrastructure/Impl/BackendProvider.cs:799` and
  `:929`, both calling `m_mdcInternal.AddCustomFields(...)`) at commit
  time — i.e. schema changes ride the same commit/save cadence as data
  changes (see F4 of the liblcm facts review), they are not written
  synchronously by `AddCustomField` itself.

This section is a pointer for implementation, not a claim that the
recipe has been tried against flexicon's wrapper — that is exactly the
work item this issue does not cover (see "Scope / fix notes").

## The correction that must not be lost (Track B vs. actual implementation)

Line 321's raise is **unimplemented work**, not a second instance of the
same guard. This distinction matters for planning:

- Moving `OpenProject`/`CloseProject` to per-operation Units of Work (the
  Phase 2 / "Track B" direction referenced in
  `docs/CUSTOM_FIELDS.md` "Future work" and `FLExProject.UndoableOperation`)
  only removes the *session-wide envelope* — i.e., it only makes it possible
  for `CurrentDepth == 0` to hold *between* operations. That unblocks the
  **precondition** checked at `:301`.
- It does **not**, by itself, implement `AddCustomField`. Once the guard at
  `:301` passes, execution falls straight into the placeholder at `:320-326`,
  which raises regardless of state.
- **Nobody should assume that landing per-operation UoWs (Track B / Phase 2)
  makes `CreateField` work.** It will still raise
  `FP_TransactionError("CreateField is not yet implemented for the no-UoW
  path...")` until the actual schema-mutation implementation — following
  the `FieldDescription.UpdateCustomField` sequence above, not a hand-rolled
  call to raw `AddCustomField` — is actually written, tested, and this stub
  is replaced.
- Track B and "make `CreateField` actually create fields" are two separate
  pieces of work with a dependency in one direction only (the latter
  depends on the former; the former does not imply the latter).

## Documentation / error-message mismatch (flagged per instructions)

Both the raised error messages and `docs/CUSTOM_FIELDS.md` correctly and
consistently tell users the *current* workaround: create custom fields via
the FLEx UI (Tools > Configure > Custom Fields), not via the wrapper. No
mismatch there — the guidance is accurate for the current state.

However, `docs/CUSTOM_FIELDS.md`'s **"Future work"** section (lines 92-107)
describes the Phase 2 recipe as though it is a design that's understood to
work once Phase 2 lands:

```
2. Before any `UndoableOperation` block, call `CreateField` (no active task ->
   `CurrentDepth == 0` -> guard passes -> schema mutation runs in a fresh
   `NonUndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW`).
```

This phrasing ("guard passes -> schema mutation runs...") reads as a
description of what `CreateField` will *do*, but as of v4.3.0 there is no
schema-mutation implementation behind the guard — only the stub raise at
`:320-326`. A reader who takes this section at face value could reasonably
conclude that Phase 2 alone is sufficient to unblock `CreateField`, which is
false per the correction above.

Additionally — and this is new in this revision — the "What the wrapper
enforces" section that precedes "Future work" (lines ~80-89, quoted above
under Correction #2) repeats the same refuted rationale
("InvalidOperationException at UndoStack.CheckNotProcessingDataChanges")
that is being corrected in this issue. Both the code comment and this doc
section trace to the same original (incorrect) belief about why the guard
is needed.

**Recommend, as required follow-up work (not performed here — this issue
does not edit `docs/CUSTOM_FIELDS.md`):**

1. Correct the "What the wrapper enforces" section's rationale to describe
   the actual hazard (ghost flid / `RegisterObjectAsModified` never run),
   not the refuted `CheckNotProcessingDataChanges` claim.
2. Tighten the "Future work" section to state explicitly that the
   `DoUsingNewOrCurrentUOW` call is a *design sketch for future
   implementation*, not existing behavior gated only by `CurrentDepth`,
   and reconcile it with the `FieldDescription.UpdateCustomField` sequence
   documented above.
3. Cross-reference this issue from both sections.

## Reproduction (illustrative — NOT executed, no live LCM/FLEx project touched)

```python
# Phase 1 (default) mode: guard at :301 fires because OpenProject()
# already opened the non-undoable envelope.
project = FLExProject()
project.OpenProject("SomeProject", writeEnabled=True)  # undoable=False (default)
try:
    project.System.CustomFields.CreateField(
        class_name="LexSense", field_name="Plural", field_type="MultiString"
    )
except FP_TransactionError as e:
    print(e)  # "CreateField cannot run inside an open UnitOfWork. ..."
project.CloseProject()

# Phase 2 (undoable=True) mode: guard at :301 would pass (CurrentDepth == 0
# between UndoableOperation blocks), but execution falls into the
# unconditional raise at :320-326 -- CreateField STILL cannot succeed.
project2 = FLExProject()
project2.OpenProject("SomeProject", writeEnabled=True, undoable=True)
try:
    project2.System.CustomFields.CreateField(
        class_name="LexSense", field_name="Plural", field_type="MultiString"
    )
except FP_TransactionError as e:
    print(e)  # "CreateField is not yet implemented for the no-UoW path. ..."
project2.CloseProject()
```

## Expected vs actual

- **Expected:** In some reachable project/transaction state, `CreateField`
  performs the schema mutation (following the
  `FieldDescription.UpdateCustomField` sequence — `AddCustomField`, then
  `UpdateCustomField`, then `RegisterObjectAsModified` for affected
  instances — inside a correctly-scoped UoW supplied by the caller) and
  returns successfully, matching the "What the wrapper enforces" / "Future
  work" framing in `docs/CUSTOM_FIELDS.md` (once that framing's rationale
  is corrected per Correction #2).
- **Actual:** `CreateField` raises `FP_TransactionError` on every call, in
  every project state reachable in v4.3.0 (both `undoable=False` and
  `undoable=True`), because (a) the Phase 1 default keeps `CurrentDepth == 1`
  for the whole session, and (b) even where `CurrentDepth == 0` could be
  achieved, the code path past the guard is an unconditional raise with no
  implementation behind it. Separately, the comment/error text explaining
  why (a) is treated as unsafe cites a mechanism
  (`CheckNotProcessingDataChanges`) that liblcm source shows is not
  actually invoked by schema mutation at all.

## Scope / fix notes

- This is **not** fixed by Track B (per-operation UoW) alone. Track B is a
  legitimate and necessary prerequisite, but closing this issue requires a
  second, separate change: implement the actual schema-mutation call at
  `CustomFieldOperations.py:320-326` — following the
  `FieldDescription.UpdateCustomField` sequence (see "Known correct
  implementation path" above), not raw `AddCustomField` alone — inside a
  UoW scoped to just that call, plus tests that exercise it against a real
  or fake `IFwMetaDataCacheManaged`/`FieldDescription`.
- Suggest splitting into three tracked issues/tasks if not already:
  1. Land Track B / Phase 2 per-operation UoWs (precondition).
  2. Implement `CreateField`'s actual schema mutation (the remaining,
     currently-stubbed work), following the `FieldDescription`-based
     sequence, and correct the in-code guard rationale at the same time
     (Correction #2) rather than leaving the misleading comment in place.
  3. Correct `docs/CUSTOM_FIELDS.md` per the "Documentation / error-message
     mismatch" section above (both the existing Phase-2-implies-it-works
     framing and the newly-identified rationale mismatch).
- This issue is scoped to documenting/confirming the *current*
  always-raises defect, correcting the refuted rationale in the guard's
  comment/error text, and recording the known correct implementation path;
  it is not a request to implement the schema mutation or edit
  `docs/CUSTOM_FIELDS.md` here.
- Until all of the above land, `docs/CUSTOM_FIELDS.md`'s current-state
  guidance (use the FLEx UI) remains correct and should stay in place.
- Related/likely-referenced issues per existing code comments: #20 (original
  `NotImplementedError` report), #21 (corruption-on-reopen postmortem that
  motivates the guard in the first place — note: #21's underlying hazard,
  ghost flids, still stands even though the guard's cited *mechanism* does
  not; see Correction #2), #236 (Phase 1 atomicity honesty pass, same area
  of `FLExProject.py`).

## Files referenced

- `flexicon/code/System/CustomFieldOperations.py:270-326`
- `flexicon/code/FLExProject.py:256-295`
- `flexicon/code/exceptions.py:87-89` (`FP_TransactionError` definition)
- `docs/CUSTOM_FIELDS.md` (whole file; "What the wrapper enforces" ~lines
  80-89 and "Future work" lines 92-107 specifically)
- `liblcm/src/SIL.LCModel/Infrastructure/Impl/UndoStack.cs:209, 252-265,
  727-734`
- `liblcm/src/SIL.LCModel/Infrastructure/Impl/LcmMetaDataCache.cs:920-965`
- `liblcm/src/SIL.LCModel/FieldDescription.cs:336, 406-413`
- `liblcm/src/SIL.LCModel/Infrastructure/Impl/BackendProvider.cs:799, 929`
- `liblcm/tests/SIL.LCModel.Tests/DomainImpl/LexEntryTests.cs:825-828, 924,
  928, 1075, 1078`
- `liblcm/tests/SIL.LCModel.Tests/Application/Impl/IDomainDataByFlidTests.cs:51-57`
- `specs/write-path-transactions/reviews/cycle2-explore-liblcm-facts.md`
  (section F6 — source of Correction #2)

---

## `gh issue create` command — NOT RUN, draft only

```
gh issue create \
  --repo MattGyverLee/flexicon \
  --title "CreateField always raises FP_TransactionError -- custom field creation impossible via wrapper in v4.3.0" \
  --body-file specs/write-path-transactions/issues/createfield-always-raises.md \
  --label bug \
  --label write-path \
  --label transactions \
  --label custom-fields \
  --label documentation
```
