# Issue #794 -- lex-lead ruling

**Date:** 2026-10-26  
**Issue:** #794 (P2) -- EnvironmentOperations Delete EnvironmentsOS HVO membership  
**Parent triage:** HVO sweep / lcm-member-truth-sweep archive (EnvironmentsOS.Remove)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#794** filed this run (Environment Delete sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the environment in `phon_data.EnvironmentsOS` by comparing
   each member's `Hvo` to the resolved environment's `Hvo`, not by passing the caller
   handle straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #760 SemanticDomain Delete and #792 Discourse Delete).
3. If no member matches, raise `FP_ParameterError`.
4. Tag the lookup with `issue #794` in comments.
5. Do not refactor unrelated EnvironmentOperations paths in this PR.

**Out of scope:** Environment Duplicate and context mutators unless a separate issue is filed.

## Verification plan

- Offline: `tests/operations/test_issue794_environment_delete_hvo_offline.py`
- Live: `tests/operations/test_issue794_environment_delete_hvo_live.py`
- Evidence: `specs/794-environment-delete-hvo/evidence/`
