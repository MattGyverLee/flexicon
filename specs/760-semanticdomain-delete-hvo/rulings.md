# Issue #760 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #760 (P2) -- SemanticDomainOperations Delete SubPossibilitiesOS/PossibilitiesOS HVO membership  
**Parent triage:** #758 AnthropologyOperations Delete HVO family (out-of-scope semantic domain delete paths)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#760** (filed this run; sibling gap after #758)

Untrusted open issues ignored per automation policy (#635 from rulingAnts).

## RULING (binding)

1. In `Delete`, locate the collection member whose `Hvo` matches the resolved
   domain before calling `Remove` on `PossibilitiesOS` or `SubPossibilitiesOS`.
2. Do not pass the caller's bare handle directly to `Remove` without an HVO scan.
3. Tag the lookup with `issue #760` in comments.
4. Do not refactor unrelated SemanticDomainOperations paths in this PR.

**Out of scope:** POSOperations RemoveSubcategory SubPossibilitiesOS HVO (next sibling gap).

## Verification plan

- Offline: `tests/operations/test_issue760_semanticdomain_delete_hvo_offline.py`
- Live: `tests/operations/test_issue760_semanticdomain_delete_hvo_live.py`
- Evidence: `specs/760-semanticdomain-delete-hvo/evidence/`
