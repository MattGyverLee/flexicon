# Issue #670 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #670 (P2) -- SplitSegment SegmentsOS index Python identity  
**Parent triage:** #525 MergeSegments HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#670** filed this run (SplitSegment sibling gap after #525)

## RULING (binding)

1. In `SplitSegment`, after the Contents edit, locate the source segment in
   `para.SegmentsOS` by comparing each member's `Hvo` to `seg.Hvo`, not
   `IndexOf(seg)`.
2. If no member matches, raise `FP_ParameterError` (do not insert at index 0
   when lookup fails).
3. Tag the lookup with `issue #670` in comments.
4. Fix only the SplitSegment SegmentsOS insert step in this PR.

**Out of scope:** MergeSegments (#525), other SegmentOperations paths.

## Verification plan

- Offline: `tests/operations/test_issue670_split_segment_hvo_offline.py`
- Live: `tests/operations/test_issue670_split_segment_hvo_live.py`
- Evidence: `specs/670-split-segment-hvo/evidence/`
