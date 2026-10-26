# Issue #750 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #750 (P2) -- PossibilityItemOperations base Delete PossibilitiesOS HVO membership  
**Parent triage:** #748 PhonologicalRuleOperations Delete HVO family (out-of-scope list)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#750** (filed this run; sibling gap after #748)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `Delete`, scan `PossibilitiesOS` on the list object for the member whose
   `Hvo` matches the resolved item, then call `Remove` with that collection
   member reference.
2. Do not use Python `in` on `PossibilitiesOS` for membership.
3. Tag the lookup with `issue #750` in comments.
4. Do not refactor unrelated PossibilityItemOperations paths in this PR.

**Out of scope:** ConstChart `DependentClausesRS` membership; nested
`SubPossibilitiesOS` delete paths.

## Verification plan

- Offline: `tests/operations/test_issue750_possibility_item_delete_hvo_offline.py`
- Live: `tests/operations/test_issue750_possibility_item_delete_hvo_live.py`
- Evidence: `specs/750-possibility-item-delete-hvo/evidence/`
