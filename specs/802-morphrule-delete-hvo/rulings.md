# Issue #802 -- lex-lead ruling

**Date:** 2026-10-26  
**Issue:** #802 (P2) -- MorphRuleOperations Delete owning-collection HVO membership  
**Parent triage:** HVO sweep / issue #800 StratumOperations Delete sibling (out-of-scope list)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#802** filed this run (MorphRule Delete sibling gap after #800)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `Delete`, for each owning collection branch (`CompoundRulesOS`,
   `AffixTemplatesOS`, `AdhocCoProhibitionsOC`), locate the member by comparing
   each slot's `Hvo` to the resolved rule's `Hvo`, not by passing the caller
   handle straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop.
3. If no member matches, return without error (preserve pre-fix parity: branches
   only ran `Remove` when containers existed; unmatched membership was a silent
   no-op on live LCM).
4. Centralize lookup in `__RemoveMemberByHvo` tagged with `issue #802`.
5. Do not refactor unrelated MorphRuleOperations paths in this PR.

**Out of scope:** PhonFeatureOperations Delete, InflectionFeatureOperations
FeatureDelete unless separate issues are filed.

## Verification plan

- Offline: `tests/operations/test_issue802_morphrule_delete_hvo_offline.py`
- Live: `tests/operations/test_issue802_morphrule_delete_hvo_live.py`
- Evidence: `specs/802-morphrule-delete-hvo/evidence/`
