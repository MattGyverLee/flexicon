# Issue #752 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #752 (P2) -- ConstChartClauseMarkerOperations AddDependentClause DependentClausesRS HVO membership  
**Parent triage:** #750 PossibilityItemOperations Delete HVO family (out-of-scope list)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#752** (filed this run; sibling gap after #750)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `AddDependentClause`, treat the dependent as already linked when any
   `DependentClausesRS` member shares the clause marker's `Hvo`.
2. Do not use Python `in` on `DependentClausesRS` for membership.
3. Tag the lookup with `issue #752` in comments.
4. Do not refactor unrelated ConstChartClauseMarkerOperations paths in this PR.

**Out of scope:** `InsertDependentClause` / `RemoveDependentClause` (index-based);
other discourse RC membership sweeps.

## Verification plan

- Offline: `tests/operations/test_issue752_dependent_clause_hvo_offline.py`
- Live: `tests/operations/test_issue752_dependent_clause_hvo_live.py`
- Evidence: `specs/752-dependent-clause-hvo/evidence/`
