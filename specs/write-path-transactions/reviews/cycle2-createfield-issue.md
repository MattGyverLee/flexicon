# Cycle 2 — CreateField-always-raises verification

**CONFIRMED** — all five chain links hold; the defect is real as described.

1. **CONFIRMED** `CustomFieldOperations.py:300-301` reads
   `ActionHandlerAccessor.CurrentDepth` and raises `FP_TransactionError` if
   `> 0`.
2. **CONFIRMED** `UndoStack.cs:727-734`: `CurrentDepth` returns 1 iff
   `CurrentProcessingState == BusinessTransactionState.ProcessingDataChanges`,
   else 0.
3. **CONFIRMED** `UndoStack.cs:262` (exact line): `BeginNonUndoableTask()`
   sets `m_uowService.CurrentProcessingState =
   BusinessTransactionState.ProcessingDataChanges;` — precisely the state
   link 2 tests for.
4. **CONFIRMED** `FLExProject.py:277` (`OpenProject`, Phase 1 /
   `writeEnabled and not undoable` branch, which is the default) calls
   `MainCacheAccessor.BeginNonUndoableTask()` unconditionally; the matching
   `EndNonUndoableTask()` is only called in `CloseProject()`
   (`FLExProject.py:293`). Envelope spans the whole session.
5. **CONFIRMED** `CustomFieldOperations.py:320-326`: unconditional
   `FP_TransactionError` raise past the guard, with its own message stating
   "not yet implemented for the no-UoW path." No `AddCustomField` call
   exists in the method — it is a stub, not a second guard.

**Documentation check:** `docs/CUSTOM_FIELDS.md`'s current-state guidance
(create fields via FLEx UI) is accurate and matches the raised error
messages — no mismatch there. However its "Future work" section
(lines 92-107) phrases the Phase 2 recipe as "guard passes -> schema
mutation runs," which reads as existing behavior. That is misleading given
link 5: the mutation is unimplemented. Flagged in the issue draft with a
recommended edit.

Draft written to:
`specs/write-path-transactions/issues/createfield-always-raises.md`
(includes title, labels, full "Verified from source" section, illustrative
reproduction, the per-op-UoW correction, docs mismatch note, scope/fix
notes, and an unrun `gh issue create` command block clearly marked NOT RUN).

No source edits, no live-LCM writes, no gh commands executed.
