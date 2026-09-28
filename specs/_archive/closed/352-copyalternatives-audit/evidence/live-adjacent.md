# Live evidence -- adjacent follow-ups to #352

**Date:** 2026-09-21
**Project:** Target sandbox (tempdir copy -- nothing leaks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Commands:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_compareto_live.py -m requires_live_project -q
python -m pytest tests/test_docstring_example_ratchet.py -q
```

## 1. Eight sibling `_CompareValues` CompareTo sites (fixed + verified)

`WordformOperations`, `WfiMorphBundleOperations`, `WfiGlossOperations`,
`ParagraphOperations`, `SegmentOperations`, `TextOperations`,
`DiscourseOperations`, `WfiAnalysisOperations` all called
`self.project._CompareValues`, which does not exist on FLExProject
(AttributeError on every compare). All eight now compare inline
(`val1 != val2`), same as the Media/DataNotebook/Person/SemDom methods.

Verified live (`test_352_compareto_live.py`, 5 passed): self-compare is
clean for Text, Paragraph, Discourse chart, Wordform, WfiAnalysis,
WfiGloss, and WfiMorphBundle objects created in the sandbox, and for a
Segment (paragraph creation produced segments on Target, so no skip was
needed).

## 2. Stale `CmAnnotationType` docstring imports (fixed, static)

Probed every loaded SIL module live: `CmAnnotationType` is exposed in
none of them, so 16 docstring sites taught an un-runnable
`from SIL.LCModel import CmAnnotationType`. All examples now pass the
type code as a plain int with a note explaining why; no behavior
changed (the value was already recorded opportunistically behind a
dead guard). Ratchet suite green (19 passed).

## Still open (environmental, not code)

- Set-valued allomorph `stem_name` round-trip needs `IMoStemName` rows
  (Sena 3; no `.fwbackup` here and the installed copy will not open).
- 4 PhaseE tests error without the Sena 3 backup (pre-existing).
- `ScrDraft.Create` `type` label stays accepted-but-unapplied (the
  ScrDraftType enum is likewise unexposed; documented in the docstring).
