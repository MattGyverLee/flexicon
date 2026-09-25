# Issue #525 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #525 (P2) -- MergeSegments SegmentsOS index/remove Python identity  
**Parent triage:** #523 Exists HVO membership; #521 MergeSegments typed-owner gate

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (filed **#525** this run)

## RULING (binding)

1. In `MergeSegments`, resolve adjacent indices by comparing each segment in
   `para.SegmentsOS` to `seg1.Hvo` / `seg2.Hvo`, not `list(...).index(seg)`.
2. When removing the merged-away segment, locate the collection member by HVO
   and call `SegmentsOS.Remove` on that member (same identity gap as #523).
3. Tag both sites with `issue #525` in comments.
4. Do not refactor unrelated SegmentOperations paths in this PR.

**Out of scope:** `__MigrateTranslations`, analysis `index()` at ~836, other modules.

## Verification plan

- Offline: `tests/operations/test_issue525_merge_segments_hvo_offline.py`
- Live: `tests/operations/test_issue525_merge_segments_hvo_live.py`
- Evidence: `specs/525-merge-segments-hvo/evidence/`
