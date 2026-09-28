# Issue #329 -- lex-lead ruling

## Decision

Rename every **LCM reference** on `IRnGenericRec` from bare `Type` /
`Status` / `Confidence` to **`TypeRA` / `StatusRA` / `ConfidenceRA`** in
`DataNotebookOperations` in one commit. Public Python API names
(`GetRecordType`, `SetStatus`, sync dict keys `Type`/`Status`/`Confidence`)
stay unchanged -- only the underlying LCM member access changes.

Pattern: match `NoteOperations` / `annotation.py` (`AnnotationTypeRA` guards
and assignment).

## Verification

Live round-trip on `target_sandbox`: write via `SetStatus` (and type/
confidence when lists exist), re-read by HVO via getters and
`GetSyncableProperties`. Offline: static lock that the module no longer
probes bare `Type`/`Status`/`Confidence` on record objects in those methods.

## Out of scope

- #328 Title/Text member crashes
- #330 GenDate read surface
- `ApplySyncableProperties` (not implemented on this class today)
