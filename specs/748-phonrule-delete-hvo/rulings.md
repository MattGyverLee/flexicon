# Issue #748 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #748 (P2) -- PhonologicalRuleOperations Delete / DeleteConstraint HVO membership  
**Parent triage:** #746 PhonemeOperations RemoveCode HVO family (out-of-scope list)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#748** (filed this run; sibling gap after #746)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `Delete`, scan `PhonRulesOS` for the member whose `Hvo` matches the resolved
   rule, then call `Remove` with that collection member reference.
2. In `DeleteConstraint`, scan `FeatConstraintsOS` by `Hvo` for membership before
   `Remove`; do not use Python `in` / `not in` on either sequence.
3. Tag both lookups with `issue #748` in comments.
4. Do not refactor unrelated PhonologicalRuleOperations paths in this PR.

**Out of scope:** PossibilityItemOperations base `Delete` HVO; ConstChart
`DependentClausesRS` membership.

## Verification plan

- Offline: `tests/operations/test_issue748_phonrule_delete_hvo_offline.py`
- Live: `tests/operations/test_issue748_phonrule_delete_hvo_live.py`
- Evidence: `specs/748-phonrule-delete-hvo/evidence/`
