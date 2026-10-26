# Issue #800 -- lex-lead ruling

**Date:** 2026-10-26  
**Issue:** #800 (P2) -- StratumOperations Delete StrataOS HVO membership  
**Parent triage:** HVO sweep / issue #798 PhonemeOperations Delete sibling (out-of-scope list)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#800** filed this run (Stratum Delete sibling gap after #798)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the stratum in `StrataOS` by comparing each member's
   `Hvo` to the resolved stratum's `Hvo`, not by passing the caller handle
   straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #794 EnvironmentOperations Delete).
3. If no member matches, return without error (preserve pre-fix parity documented
   on `Delete`).
4. Tag the lookup with `issue #800` in comments.
5. Do not refactor unrelated StratumOperations paths in this PR.

**Out of scope:** MorphRuleOperations Delete, PhonFeatureOperations Delete,
InflectionFeatureOperations Delete unless separate issues are filed.

## Verification plan

- Offline: `tests/operations/test_issue800_stratum_delete_hvo_offline.py`
- Live: `tests/operations/test_issue800_stratum_delete_hvo_live.py`
- Evidence: `specs/800-stratum-delete-hvo/evidence/`
