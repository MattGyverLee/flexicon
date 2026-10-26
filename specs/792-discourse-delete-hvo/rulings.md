# Issue #792 -- lex-lead ruling

**Date:** 2026-10-26  
**Issue:** #792 (P2) -- DiscourseOperations DeleteChart/DeleteRow HVO membership  
**Parent triage:** #790 SegmentOperations Delete SegmentsOS HVO (open PR #791)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#792** filed this run (Discourse Delete sibling gap from #790 ruling out-of-scope)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `DeleteChart`, locate the chart in the owning text's `ChartsOC` by comparing
   each member's `Hvo` to the resolved chart's `Hvo`, not by passing the caller
   handle straight to `Remove`.
2. In `DeleteRow`, locate the row in the owning chart's `RowsOS` the same way.
3. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #790 Segment Delete and #788 Paragraph Delete).
4. If no member matches, raise `FP_ParameterError`.
5. Tag the lookup with `issue #792` in comments.
6. Do not refactor unrelated DiscourseOperations paths in this PR.

**Out of scope:** Other Discourse write paths (Duplicate, cell mutators) unless a separate issue is filed.

## Verification plan

- Offline: `tests/operations/test_issue792_discourse_delete_hvo_offline.py`
- Live: `tests/operations/test_issue792_discourse_delete_hvo_live.py`
- Evidence: `specs/792-discourse-delete-hvo/evidence/`
