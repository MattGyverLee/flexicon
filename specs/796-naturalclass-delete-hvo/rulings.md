# Issue #796 -- lex-lead ruling

**Date:** 2026-10-26  
**Issue:** #796 (P2) -- NaturalClassOperations Delete NaturalClassesOS HVO membership  
**Parent triage:** HVO sweep / issue #794 EnvironmentOperations Delete sibling

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#796** filed this run (NaturalClass Delete sibling gap after #794)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the natural class in `phon_data.NaturalClassesOS` by comparing
   each member's `Hvo` to the resolved class's `Hvo`, not by passing the caller
   handle straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #794 EnvironmentOperations Delete).
3. If no member matches, raise `FP_ParameterError`.
4. Tag the lookup with `issue #796` in comments.
5. Do not refactor unrelated NaturalClassOperations paths in this PR.

**Out of scope:** NaturalClass Duplicate, SegmentsRC mutators, and other Grammar Delete
paths (StratumOperations, MorphRuleOperations) unless separate issues are filed.

## Verification plan

- Offline: `tests/operations/test_issue796_naturalclass_delete_hvo_offline.py`
- Live: `tests/operations/test_issue796_naturalclass_delete_hvo_live.py`
- Evidence: `specs/796-naturalclass-delete-hvo/evidence/`
