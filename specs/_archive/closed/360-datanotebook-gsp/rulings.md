# Issue #360 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/360-datanotebook-gsp from origin/main

## RULING (binding)

Campaign #325 pattern-audit flagged `DataNotebookOperations.GetSyncableProperties`
(~2722) for unverified `Type` / `Status` / `Confidence` guards because
`ICmDataNotebookRecord` was absent from the T0 baseline snapshot.

**Finding:** Notebook records are `IRnGenericRec`. The liblcm baseline lists
`TypeRA`, `StatusRA`, `ConfidenceRA`, and `DateOfEvent` on that interface.
Production code on `main` (issue #329) already reads the RA members in GSP;
there is no remaining bare `Type` / `Status` / `Confidence` guard in
`GetSyncableProperties`.

**Fix for this PR (verification + regression lock, no LCM behaviour change):**

1. Add a dedicated `hasattr(record, ...)` ratchet case in
   `tests/test_syncable_properties_member_ratchet.py` (maps to `IRnGenericRec`;
   the parametrized `hasattr(item, ...)` sweep stays unchanged to avoid nested
   false positives in `ExampleOperations` / `TextOperations`).
2. Offline source lock in `tests/operations/test_issue360_datanotebook_gsp_offline.py`.
3. Live read-only smoke over every data-notebook record when LCM is available
   (`tests/operations/test_issue360_datanotebook_gsp_live.py`).

**Out of scope:** `ApplySyncableProperties` (not implemented on DataNotebook);
new sync keys beyond the existing Title/Text/Type/Status/Confidence/DateOfEvent set.

## Verification plan

- Offline:
  `python -m pytest tests/test_syncable_properties_member_ratchet.py tests/operations/test_issue360_datanotebook_gsp_offline.py -m "not requires_live_project" -q`
- Live (when FieldWorks available):
  `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue360_datanotebook_gsp_live.py -m requires_live_project -q`
