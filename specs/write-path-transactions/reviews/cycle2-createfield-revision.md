# Cycle 2 revision report: createfield-always-raises.md

**Core defect: SURVIVED re-verification, independent of the refuted premise.**
Re-read `flexicon/flexicon/code/System/CustomFieldOperations.py:270-326`
directly (not just trusted the draft): the `:301` `CurrentDepth > 0` guard
and the unconditional stub raise at `:320-326` are both present verbatim as
described. `CreateField` still cannot return successfully under any
reachable v4.3.0 state.

**What changed:**
1. Removed the refuted premise from the guard's justification. Added
   "Correction #2" section stating the `:288-289`/`:305-306` claim
   ("raises InvalidOperationException at UndoStack.CheckNotProcessingDataChanges")
   is false per F6 — `LcmMetaDataCache.AddCustomField` never touches
   UnitOfWorkService, and liblcm's own tests (LexEntryTests.cs:825-1078)
   mutate schema inside an open UoW successfully.
2. Framed this as a second, distinct defect (misleading rationale), not
   grounds to remove the guard — explicitly noted the ghost-flid hazard
   (RegisterObjectAsModified skipped) may still justify the guard.
3. Added "Known correct implementation path" citing
   `FieldDescription.cs:336,406-413` and `BackendProvider.cs:799,929`,
   spot-checked directly against liblcm source in this pass (all line
   numbers confirmed).
4. Kept the Track-B-doesn't-imply-implementation correction prominent.
5. Added docs/CUSTOM_FIELDS.md mismatch as required follow-up (not edited).
6. `gh issue create` block retained, still marked NOT RUN.

No source files edited; no gh/git commands run.
