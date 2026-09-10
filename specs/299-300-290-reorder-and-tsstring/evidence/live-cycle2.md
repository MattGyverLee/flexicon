# Live verification -- cycle 2 consolidated (#300, #299, #290)

**Project:** Target | **Fixture:** target_sandbox
**Command:** `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_cycle2_live_299_300_290.py -m requires_live_project -q`
**run_mode:** live
**Date:** 2026-09-10

## Claim under test

1. (#300) `WfiMorphBundleOperations._GetSequence` returns `IWfiAnalysis.MorphBundlesOS` (not the nonexistent `MorphsOS`); `DataNotebookOperations._GetSequence` returns `IRnGenericRec.SubRecordsOS` (not the nonexistent `RecordsOS`).
2. (#299) `ParagraphOperations._GetSequence` returns a text's `ContentsOA.ParagraphsOS`; `SegmentOperations._GetSequence` returns a paragraph's `SegmentsOS` (not `AnalysesRS`); `TextOperations._GetSequence` is removed entirely, so `project.Texts.Sort()`/`MoveUp()` raise `NotImplementedError` live.
3. (#290) `ConstChartRowOperations.Create/GetLabel/SetLabel/GetNotes/SetNotes` route `IConstChartRow.Label`/`.Notes` through `_MakeTsString`/`_ReadTsString` (bare `ITsString`, not `IMultiString`).

## Pre-state / Action / Post-state (read back from the LCM after each write)

### (A) #300 -- WfiMorphBundleOperations (analysis hvo 10443)
- `hasattr(analysis, "MorphsOS")` = `False`, `hasattr(analysis, "MorphBundlesOS")` = `True`
- Created 3 bundles, `analysis.MorphBundlesOS` re-read as `[10444, 10445, 10446]`
- `MoveDown(analysis, b1, 1)` -> re-read `[10445, 10444, 10446]`
- `MoveUp(analysis, b3, 2)` -> re-read `[10446, 10445, 10444]`
- `MoveToIndex(analysis, b2, 0)` -> re-read `[10445, 10446, 10444]`

### (A) #300 -- DataNotebookOperations (parent hvo 10442)
- `hasattr(parent, "RecordsOS")` = `False`, `hasattr(parent, "SubRecordsOS")` = `True`
- Created 3 sub-records, `parent.SubRecordsOS` re-read as `[10443, 10444, 10445]`
- `MoveDown` -> `[10444, 10443, 10445]`
- `MoveUp` -> `[10445, 10444, 10443]`
- `MoveToIndex` -> `[10444, 10445, 10443]`
- Route-around note: two SEPARATE pre-existing live defects were found and
  routed around (neither in scope for #300, both confirmed live via
  reflection before working around them):
  1. `DataNotebookOperations.Create()` calls
     `repos.RecordsOC.Add(record)` on `IRnResearchNbkRepository`, which
     has no `RecordsOC` member live (`AttributeError`). Real collection
     is `LangProject.ResearchNotebookOA.RecordsOC`.
  2. `DataNotebookOperations.__GetRecordObject` (used by
     `CreateSubRecord`/`SetTitle`/etc.) calls
     `self.project.project.GetObject(hvo)`; `LcmCache` has no
     `GetObject` member live (`AttributeError`). House pattern is
     `self.project.Object(hvo)`.
  The parent + 3 sub-records were built directly via
  `IRnGenericRecFactory` + `RecordsOC`/`SubRecordsOS.Add()` so the test
  could reach the actual `_GetSequence` code path (exercised through
  `BaseOperations.MoveUp/MoveDown/MoveToIndex`'s generic `_GetObject`,
  unaffected by either bug above) without being blocked by these two
  unrelated defects. Flagged for separate follow-up, not fixed here.

### (B) #299 -- ParagraphOperations (text hvo, paragraphs 10444/10446/10448)
- Created 3 paragraphs, `text.ContentsOA.ParagraphsOS` re-read as `[10444, 10446, 10448]`
- `MoveDown` -> `[10446, 10444, 10448]`
- `MoveUp` -> `[10448, 10446, 10444]`
- `MoveToIndex` -> `[10446, 10448, 10444]`
- `Sort(key_func=lambda p: p.Hvo)` -> returned count `3`, re-read `[10444, 10446, 10448]` (ascending, confirming `Sort` really re-persisted via `MoveTo`)

### (B) #299 -- SegmentOperations (paragraph, segments tail 10447/10448/10449)
- `hasattr(para, "AnalysesRS")` = `False`, `hasattr(para, "SegmentsOS")` = `True`
- After 3 `AppendSentence` calls, `para.SegmentsOS` re-read as `[10445, 10446, 10447, 10448, 10449]` (paragraph creation's own placeholder sentence auto-parses into leading segments 10445/10446, confirmed pre-existing and orthogonal to this test -- the tail `[10447, 10448, 10449]` is exactly the 3 segments this test created, in creation order)
- `MoveDown(para, s1, 1)` on the tail -> re-read tail `[10448, 10447, 10449]`
- `MoveToIndex(para, s3, base_n)` -> re-read tail `[10449, 10448, 10447]`
- Confirms reordering hits `SegmentsOS`; `AnalysesRS` was never referenced (attribute does not exist on `IStTxtPara`, confirmed above)

### (B) #299 -- TextOperations (negative test, required)
- `project.Texts.Sort(langProject, key_func=...)` raised
  `NotImplementedError: TextOperations must implement _GetSequence() to
  specify which owning sequence to reorder. Example: return
  parent.SensesOS` (the inherited `BaseOperations._GetSequence` default)
- `project.Texts.MoveUp(langProject, t1, 1)` raised the identical
  `NotImplementedError`
- Confirms the override is gone and Texts.Sort/MoveUp fail loudly live
  rather than silently mis-operating on `ContentsOS` (a `TextsOC`-style
  collection with no `.MoveTo()`)

### (C) #290 -- ConstChartRowOperations (row on a fresh TEST_ chart)
- `Create(chart, label="TEST_C2_Verse 1", notes="TEST_C2_initial notes")`
  -> `GetLabel(row)` re-read = `"TEST_C2_Verse 1"`, `GetNotes(row)`
  re-read = `"TEST_C2_initial notes"`
- `SetLabel(row, "TEST_C2_Verse 1 revised")`,
  `SetNotes(row, "TEST_C2_revised notes")` -> re-read
  `"TEST_C2_Verse 1 revised"` / `"TEST_C2_revised notes"`
- `SetLabel(row, "")`, `SetNotes(row, "")` -> re-read `""` / `""`
- `hasattr(row.Label, "get_String")` = `False`,
  `hasattr(row.Label, "set_String")` = `False` -- confirms the field is
  genuinely a bare `ITsString` live, matching cycle-1 reflection

Raw JSON evidence: `specs/299-300-290-reorder-and-tsstring/evidence/live-cycle2-raw.json`

## Cleanup

All objects created inside `target_sandbox` -- a fresh tempdir copy of
the Target `.fwbackup`, discarded at fixture teardown. The real Target
project was never opened. `target_sandbox`'s `_FwBackupSandbox` context
manager deletes the tempdir on exit, so no manual restore step is
required or possible to skip.

## Result

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_cycle2_live_299_300_290.py -m requires_live_project -q
......                                                                   [100%]
6 passed in 6.96s
```

`tests/live_status.json` -> `"run_mode": "live"` (confirmed via
`python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"`).

Mock/offline regression sweep (unchanged from cycle 1/2 programmer runs):
```
python -m pytest tests/operations/test_300_getsequence_property_rename.py tests/operations/test_299_getsequence_ownership_fix.py tests/operations/test_290_const_chart_row_tsstring.py -q
............................                                             [100%]
28 passed in 1.39s
```

[PASS] -- all three issues' write-path claims (#300, #299, #290)
confirmed against a live LCM, values re-queried from the database after
each write, not asserted from the input.

## Bug reports filed for follow-up (out of scope, not fixed this cycle)

Two pre-existing live defects in `DataNotebookOperations` were
discovered while building fixtures for the #300 test (see route-around
note above): the `Create()` top-level `repos.RecordsOC` typo, and the
`__GetRecordObject` `self.project.project.GetObject(hvo)` typo. Neither
touches `_GetSequence` (the only method #300 changed) and neither is
fixed by this cycle's diff; they block essentially all
`DataNotebookOperations` CRUD live right now and should be filed as a
new issue.
