# Issue #523 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #523 (P2) -- SegmentOperations Exists Python identity on SegmentsOS  
**Parent triage:** #521 MergeSegments / GetOwningParagraph typed-owner family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (filed **#523** this run)

## RULING (binding)

1. In `SegmentOperations.Exists`, replace `segment_obj in list(para.SegmentsOS)`
   with HVO equality against each segment in `para.SegmentsOS`.
2. Resolve inputs via existing `__GetParagraphObject` / `__GetSegmentObject`
   (no API change).
3. Do not widen to other modules in this PR; only this chokepoint showed the
   `in list(collection)` pattern in TextsWords segment helpers.

**Out of scope:** Casting segments returned from `GetAll`; MergeSegments index
(uses LCM `IndexOf`, already live-verified in #521).

## Verification plan

- Offline: `tests/operations/test_issue523_segment_exists_hvo_offline.py`
- Live: `tests/operations/test_issue523_segment_exists_hvo_live.py`
- Evidence: `specs/523-segment-exists-hvo/evidence/`
