# Issue #230 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** fix/230-reference-sequence-close-out from origin/main

## Status

Sibling gap **1** (`ConstChartClauseMarkerOperations.DependentClausesRS`) landed
on `main` via PR #414. Issue #230 remained open because the merge did not carry
`closes #230` and sibling gap **2** was still listed in the issue body.

## RULING (binding, close-out only)

1. **Gap 1 -- closed by #414.** `InsertDependentClause` and
   `RemoveDependentClause` mirror the #215 `SegmentOperations` AnalysesRS writers.
   No further LCM change for discourse clause markers in this PR.
2. **Gap 2 -- not a flexicon defect.** Live LCM reflection and write-path work
   (`specs/352-copyalternatives-audit/evidence/live-write.md`) confirm
   **`ICmSemanticDomain` has no `OccurrencesRS` member**. The audit item copied
   a `IWfiWordform` pattern onto semantic domains; `GetSyncableProperties` must
   not imply a sequence that does not exist on the type.
3. Add the missing `[Unreleased]` CHANGELOG bullet for gap 1 and an offline
   ratchet so `SemanticDomainOperations` never reintroduces `OccurrencesRS` access.
4. Close #230 with this PR.

## Verification

- Offline: `python -m pytest tests/operations/test_issue230_dependent_clauses_rs.py tests/operations/test_issue230_semantic_domain_occurrences_ratchet.py -m "not requires_live_project" -q`
- Live: unchanged from PR #414 (`specs/230-reference-sequence-writes/evidence/offline-230.md`); **FAIL: unverified** on cloud agent (no FieldWorks runtime).
