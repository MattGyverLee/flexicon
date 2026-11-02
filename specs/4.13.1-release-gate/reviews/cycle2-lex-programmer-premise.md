# Cycle 2 -- premise investigation (#752, #684, #670)

Reflection: live, Target opened read-only (`clr.GetClrType(...).GetProperties()`).

## #752 ConstChartClauseMarker dependent clauses -- NEEDS-REDESIGN (code untouched)
- Evidence: `IConstChartClauseMarker.DependentClausesRS : ILcmReferenceSequence<IConstChartRow>`. Only other property: HasValidRefs.
- Premise is wrong: AddDependentClause/InsertDependentClause take a clause *marker* and call `.Add/.Insert(marker)`, so every call raises (pythonnet "No method matches"). RemoveDependentClause(index) and GetDependentClauses are type-correct (return IConstChartRow, not markers).
- Proposed API: `clause_row` parameter, typed `IConstChartRow`; return rows from Get. Breaking: Add/Insert argument type; existing marker-typed callers already fail every call, so real breakage is nil. A marker cannot be converted to a row, so this is a semantics change, not an internal cast.
- Suggested label: P1 (public op fails on every call).

## #684 ExampleOperations media -- NEEDS-REDESIGN (code untouched)
- Evidence: ILexExampleSentence properties: PublishIn, Example, Reference, TranslationsOC, LiftResidue, DoNotPublishInRC. Concrete LexExampleSentence adds only DoNotPublishInRC. There is NO MediaFilesOS (media lives on ILexPronunciation; pictures on ILexSense.PicturesOS).
- Every `hasattr(example,"MediaFilesOS")` guard is False: GetMediaFiles -> [], GetMediaCount -> 0, RemoveMediaFile -> silent no-op, AddMediaFile and MoveMediaFile -> raise FP_ParameterError ("does not support media files"). The #684 HVO fix is unreachable.
- Proposed: remove the five methods (or deprecate and raise NotImplementedError with a pointer to pronunciation/sense APIs). Breaking only for callers of an API that never worked. #684 live test should be retired or expect FP_ParameterError. Label: P2 (broken API, workaround = use pronunciation media).

## #670 SplitSegment -- FIXED-LOCAL (real defect; baseline was right)
- Evidence (probe, sandbox): assigning `para.Contents` alone turned one segment [0,26] into (10445,0,18 "TEST_670_Alpha b. ") + (10446,18,28 "eta gamma."): LCM re-segments itself. The extra `factory.Create()` + `SegmentsOS.Insert` produced three segments: [10445 (0,0) empty, 10447 (0,18), 10446 (18,28)] -- seg2 was the bogus one, so seg1/seg2 ordering was also wrong.
- Fix (SegmentOperations.SplitSegment, signature unchanged): drop the manual insert; after the Contents edit return `(seg, SegmentsOS[idx+1])`; FP_ParameterError if no re-segmentation. HVO lookup retained (offline ratchet intact). Docstring updated.
- Test: live test now also asserts no zero-length segment and seg1/seg2 text.
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue670_split_segment_hvo_live.py -m requires_live_project -q` -> 1 passed; run_mode: live (tests/live_status.json).
- Offline: `-m "not requires_live_project" -k "segment or issue670"` -> 86 passed (full offline suite not run).
- Files changed: flexicon/code/TextsWords/SegmentOperations.py, tests/operations/test_issue670_split_segment_hvo_live.py. Nothing committed.
