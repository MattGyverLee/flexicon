# Issue #528 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #528 (P2) -- ReplaceAnalysis AnalysesRS Python identity  
**Parent triage:** #525 MergeSegments HVO index/remove; #523 Exists HVO membership

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (filed **#528** this run)

## RULING (binding)

1. In `ReplaceAnalysis`, locate the old analysis in `AnalysesRS` by comparing
   each token's `Hvo` to `old_obj.Hvo`, not `list(...)` membership / `index()`.
2. Resolve inputs via existing `__GetSegmentObject` / `__GetAnalysisObject`
   (no API change).
3. Tag the site with `issue #528` in comments.
4. Extend mock coverage so two Python wrappers sharing an HVO exercise the path.

**Out of scope:** Other AnalysesRS writers; WfiMorphBundleOperations.index;
ParagraphOperations para_list.index.

## Verification plan

- Offline: `tests/operations/test_issue528_replace_analysis_hvo_offline.py`
- Live: `tests/operations/test_issue528_replace_analysis_hvo_live.py`
- Evidence: `specs/528-replace-analysis-hvo/evidence/`
