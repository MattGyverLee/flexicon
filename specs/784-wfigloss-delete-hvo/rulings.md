# Issue #784 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #784 (P2) -- WfiGlossOperations Delete HVO membership  
**Parent triage:** #782 WfiAnalysisOperations Delete AnalysesOC HVO (open PR #783)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#784** filed this run (WfiGloss Delete sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the gloss in the owning analysis's `MeaningsOC` by comparing
   each member's `Hvo` to the resolved gloss's `Hvo`, not by passing the caller
   handle straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #782 WfiAnalysis Delete and #772 Overlay Delete).
3. If no member matches, raise `FP_ParameterError` (gloss not linked to analysis).
4. Tag the lookup with `issue #784` in comments.
5. Do not refactor unrelated WfiGlossOperations paths in this PR.

**Out of scope:** WfiMorphBundle Delete (#785 candidate), WfiAnalysis Delete (#782 / PR #783).

## Verification plan

- Offline: `tests/operations/test_issue784_wfigloss_delete_hvo_offline.py`
- Live: `tests/operations/test_issue784_wfigloss_delete_hvo_live.py`
- Evidence: `specs/784-wfigloss-delete-hvo/evidence/`
