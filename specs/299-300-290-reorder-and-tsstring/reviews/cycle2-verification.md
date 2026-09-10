# Verification Report -- 299-300-290-reorder-and-tsstring (cycle 2, consolidated)

**Verdict:** [PASS]
**Live run:** yes | **run_mode:** live
**Evidence:** specs/299-300-290-reorder-and-tsstring/evidence/live-cycle2.md
(raw JSON: specs/299-300-290-reorder-and-tsstring/evidence/live-cycle2-raw.json)
**Project:** Target | **Fixture:** target_sandbox

## Claim vs. observed

| Claim | Observed live | Status |
|-------|---------------|--------|
| #300 WfiMorphBundleOperations._GetSequence -> MorphBundlesOS, not MorphsOS | `hasattr(analysis, "MorphsOS")` False, `MorphBundlesOS` True; MoveUp/MoveDown/MoveToIndex re-read correct order each step | [PASS] |
| #300 DataNotebookOperations._GetSequence -> SubRecordsOS, not RecordsOS | `hasattr(parent, "RecordsOS")` False, `SubRecordsOS` True; MoveUp/MoveDown/MoveToIndex re-read correct order each step | [PASS] |
| #299 ParagraphOperations._GetSequence -> text.ContentsOA.ParagraphsOS | 3 paragraphs created, Move*/Sort all re-read from ParagraphsOS with correct resulting order, Sort returned count 3 | [PASS] |
| #299 SegmentOperations._GetSequence -> paragraph.SegmentsOS, not AnalysesRS | `hasattr(para, "AnalysesRS")` False (attribute does not exist on IStTxtPara), `SegmentsOS` True; 3 segments reordered and re-read correctly | [PASS] |
| #299 TextOperations._GetSequence removed -> Sort()/MoveUp() raise NotImplementedError live | Both calls raised NotImplementedError live with the inherited BaseOperations message | [PASS] |
| #290 ConstChartRowOperations Label/Notes route through _MakeTsString/_ReadTsString (bare ITsString) | Create/Get round-trip, Set round-trip, clear-to-empty round-trip all re-read correctly; row.Label has no get_String/set_String live | [PASS] |

## Mock suite (regression, supplementary)

Command: `python -m pytest tests/operations/test_300_getsequence_property_rename.py tests/operations/test_299_getsequence_ownership_fix.py tests/operations/test_290_const_chart_row_tsstring.py -q`
Result: 28 passed, 0 failed
Pre-existing failures (not caused by this change): none observed in this targeted run

## Blockers

None. Target was present and unlocked (`scripts/restore_target.py --check`
confirmed baseline before the session); `target_sandbox` was used
throughout per the dispatch instructions, so the real Target was never
opened or written to.

## Notable findings during verification (not blockers, filed as follow-up)

Two pre-existing, unrelated live defects were discovered while building
fixtures for the #300 `DataNotebookOperations` test and routed around
(not fixed, per instructions -- see evidence file for full detail and
the exact route-around code):

1. `DataNotebookOperations.Create()` calls `repos.RecordsOC.Add(record)`
   on `IRnResearchNbkRepository`, which has no `RecordsOC` member live
   (`AttributeError`). The correct collection is
   `LangProject.ResearchNotebookOA.RecordsOC`.
2. `DataNotebookOperations.__GetRecordObject` (used internally by
   `CreateSubRecord`, `SetTitle`, and other record-resolving methods)
   calls `self.project.project.GetObject(hvo)`; `LcmCache` has no
   `GetObject` member live (`AttributeError`). The house pattern used
   elsewhere is `self.project.Object(hvo)`.

Neither defect touches `_GetSequence` (the only method #300's diff
changed in this file), and neither was introduced by the working-tree
changes under verification -- both reproduce identically on `main`.
They currently block essentially all `DataNotebookOperations` write
CRUD live (`Create`, `CreateSubRecord`, `SetTitle`, and likely every
other `__GetRecordObject`-based method) and should be filed as a new
issue for separate follow-up.

## Recommendation

APPROVE. All six live claims across #300, #299, and #290 were verified
against a real FieldWorks LCM (`target_sandbox`, run_mode: live), each
assertion re-querying the object from the database after the write
rather than trusting the input value. The mock/offline regression
suite for all three issues' new test files remains green (28/28). File
a new issue for the two `DataNotebookOperations` defects found in
route-around (not part of this feature's scope).
