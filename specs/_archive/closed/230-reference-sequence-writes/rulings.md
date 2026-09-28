# Issue #230 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/230-dependent-clauses-rs from origin/main

## RULING (binding)

Sibling gap **1** from the #215 sweep audit: `ConstChartClauseMarkerOperations`
exposes `AddDependentClause` for `DependentClausesRS` but no index-based remove
or insert. Users must drop to raw LCM to reorder or drop dependents.

**In scope (this PR):**

1. Add `InsertDependentClause(marker, index, clause_marker)` -- mirror
   `SegmentOperations.InsertAnalysis` bounds (`0 <= index <= Count`).
2. Add `RemoveDependentClause(marker, index)` -- mirror
   `SegmentOperations.RemoveAnalysis` bounds (`0 <= index < Count`).
3. Reuse the existing `IConstChartClauseMarker` type guard from
   `AddDependentClause`. Keep membership/idempotency behaviour on `Add` unchanged.
4. Offline mock tests following `test_segment_operations.py` (#215 pattern).

**Out of scope:**

- Gap **2** (`SemanticDomainOperations.OccurrencesRS`) -- needs product decision.
- `ReplaceDependentClause` / `SetDependentClause` -- not required to close the
  documented remove gap; follow-up if callers need object-keyed replace.

## Verification plan

- Offline: `tests/operations/test_issue230_dependent_clauses_rs.py`
- Live: write-path on `target_sandbox` when LCM available (`requires_live_project`).
  Cloud agent: **FAIL: unverified** (no FieldWorks on Linux pod).
