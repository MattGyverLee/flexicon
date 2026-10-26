# Issue #786 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #786 (P2) -- WfiMorphBundleOperations Delete HVO membership  
**Parent triage:** #784 WfiGlossOperations Delete MeaningsOC HVO (open PR #785)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#786** filed this run (WfiMorphBundle Delete sibling gap from #784 ruling out-of-scope)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the morph bundle in the owning analysis's `MorphBundlesOS` by comparing
   each member's `Hvo` to the resolved bundle's `Hvo`, not by passing the caller
   handle straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #782 WfiAnalysis Delete, #784 WfiGloss Delete, and #533 Duplicate insert_after).
3. If no member matches, raise `FP_ParameterError` (bundle not linked to analysis).
4. Tag the lookup with `issue #786` in comments.
5. Do not refactor unrelated WfiMorphBundleOperations paths in this PR.

**Out of scope:** WfiMorphBundle Reorder (#698 / PR #699), ParagraphOperations Delete,
DiscourseOperations DeleteChart/DeleteRow.

## Verification plan

- Offline: `tests/operations/test_issue786_wfimorphbundle_delete_hvo_offline.py`
- Live: `tests/operations/test_issue786_wfimorphbundle_delete_hvo_live.py`
- Evidence: `specs/786-wfimorphbundle-delete-hvo/evidence/`
