# Issue #754 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #754 (P2) -- PossibilityListOperations DeleteItem SubPossibilitiesOS/PossibilitiesOS HVO membership  
**Parent triage:** #752 ConstChart AddDependentClause HVO family (out-of-scope list from #750)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#754** (filed this run; sibling gap after #750 nested delete paths)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `DeleteItem`, locate the collection member whose `Hvo` matches the resolved
   item before calling `Remove` on `SubPossibilitiesOS` or top-level `PossibilitiesOS`.
2. Do not pass the caller's bare handle directly to `Remove` without an HVO scan.
3. Tag the lookup with `issue #754` in comments.
4. Do not refactor unrelated PossibilityListOperations paths in this PR.

**Out of scope:** Location/SemanticDomain/Anthropology SubPossibilitiesOS delete paths;
PossibilityItemOperations base (covered by #750 PR).

## Verification plan

- Offline: `tests/operations/test_issue754_possibility_list_delete_hvo_offline.py`
- Live: `tests/operations/test_issue754_possibility_list_delete_hvo_live.py`
- Evidence: `specs/754-possibility-list-delete-hvo/evidence/`
