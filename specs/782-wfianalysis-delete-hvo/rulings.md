# Issue #782 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #782 (P2) -- WfiAnalysisOperations Delete HVO membership  
**Parent triage:** #780 AgentOperations Delete AnalyzingAgentsOC HVO (open PR #781)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#782** filed this run (WfiAnalysis Delete sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the analysis in the owning wordform's `AnalysesOC` by comparing
   each member's `Hvo` to the resolved analysis's `Hvo`, not by passing the caller
   handle straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #772 Overlay Delete and #780 Agent Delete).
3. If no member matches, raise `FP_ParameterError` (analysis not linked to wordform).
4. Tag the lookup with `issue #782` in comments.
5. Do not refactor unrelated WfiAnalysisOperations paths in this PR.

**Out of scope:** EvaluationsRC / agent attach helpers (#780 ruling), Duplicate append,
WordformOperations analysis duplication.

## Verification plan

- Offline: `tests/operations/test_issue782_wfianalysis_delete_hvo_offline.py`
- Live: `tests/operations/test_issue782_wfianalysis_delete_hvo_live.py`
- Evidence: `specs/782-wfianalysis-delete-hvo/evidence/`
