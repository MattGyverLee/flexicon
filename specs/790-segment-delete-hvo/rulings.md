# Issue #790 -- lex-lead ruling

**Date:** 2026-10-26  
**Issue:** #790 (P2) -- SegmentOperations Delete HVO membership  
**Parent triage:** #788 ParagraphOperations Delete ParagraphsOS HVO (open PR #789)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#790** filed this run (Segment Delete sibling gap from #788 ruling out-of-scope)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the segment in the owning paragraph's `SegmentsOS` by comparing
   each member's `Hvo` to the resolved segment's `Hvo`, not by passing the caller
   handle straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #788 Paragraph Delete and #786 WfiMorphBundle Delete).
3. If no member matches, raise `FP_ParameterError` (segment not linked to paragraph).
4. Tag the lookup with `issue #790` in comments.
5. Do not refactor unrelated SegmentOperations paths in this PR.

**Out of scope:** DiscourseOperations DeleteChart/DeleteRow (separate triage if needed).

## Verification plan

- Offline: `tests/operations/test_issue790_segment_delete_hvo_offline.py`
- Live: `tests/operations/test_issue790_segment_delete_hvo_live.py`
- Evidence: `specs/790-segment-delete-hvo/evidence/`
