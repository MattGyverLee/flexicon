# Issue #756 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #756 (P2) -- LocationOperations Delete SubPossibilitiesOS/PossibilitiesOS HVO membership  
**Parent triage:** #754 PossibilityListOperations DeleteItem HVO family (out-of-scope list)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#756** (filed this run; sibling gap after #754 Location delete paths)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the collection member whose `Hvo` matches the resolved
   location before calling `Remove` on `SubPossibilitiesOS` or top-level
   `PossibilitiesOS`.
2. Do not pass the caller's bare handle directly to `Remove` without an HVO scan.
3. Tag the lookup with `issue #756` in comments.
4. Do not refactor unrelated LocationOperations paths in this PR.

**Out of scope:** SemanticDomainOperations / AnthropologyOperations nested delete paths;
PossibilityListOperations DeleteItem (covered by #754 PR).

## Verification plan

- Offline: `tests/operations/test_issue756_location_delete_hvo_offline.py`
- Live: `tests/operations/test_issue756_location_delete_hvo_live.py`
- Evidence: `specs/756-location-delete-hvo/evidence/`
