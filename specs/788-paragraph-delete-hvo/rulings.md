# Issue #788 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #788 (P2) -- ParagraphOperations Delete HVO membership  
**Parent triage:** #786 WfiMorphBundleOperations Delete MorphBundlesOS HVO (open PR #787)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#788** filed this run (Paragraph Delete sibling gap from #786 ruling out-of-scope)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the paragraph in the owning text's `ParagraphsOS` by comparing
   each member's `Hvo` to the resolved paragraph's `Hvo`, not by passing the caller
   handle straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #786 WfiMorphBundle Delete, #784 WfiGloss Delete, and #531 Duplicate insert_after).
3. If no member matches, raise `FP_ParameterError` (paragraph not linked to text).
4. Tag the lookup with `issue #788` in comments.
5. Do not refactor unrelated ParagraphOperations paths in this PR.

**Out of scope:** DiscourseOperations DeleteChart/DeleteRow, TextOperations Delete,
SegmentOperations Delete (separate triage if needed).

## Verification plan

- Offline: `tests/operations/test_issue788_paragraph_delete_hvo_offline.py`
- Live: `tests/operations/test_issue788_paragraph_delete_hvo_live.py`
- Evidence: `specs/788-paragraph-delete-hvo/evidence/`
