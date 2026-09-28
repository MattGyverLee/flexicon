# Issue #494 -- lex-lead ruling (cron)

**Date:** 2026-09-25  
**Issue:** #494 (P3) -- contract-only uncast resolver docstring hygiene  
**Parent triage:** #284 re-triage (`specs/284-uncast-resolver-retriage/RETRIAGE.md`)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#492 fix merged as PR #496; issue still open -- close after live gate)
- Open **P3** bugs without an open PR: **#494** (selected)
- Did not re-open **#492** (behavioural fix already on `main`)

## RULING (binding)

1. **No casts.** These five helpers are deliberate generics or identity-preserving
   resolvers; casting would be wrong (#494 scope table).
2. **Docstring truth.** Each helper's docstring must state that the HVO (and, where
   applicable, GUID) path returns the bare object from ``project.Object(...)`` --
   a pythonnet ``ICmObject`` view when uncast -- and that callers needing subtype
   members must cast themselves (``#212`` pattern for ``__GetAnalysisObject``).
3. **Out of scope.** Behavioural rows (#490, #492, #493); production cast changes;
   module splits; live LCM gates (contract-only batch).

## Verification plan

- Offline:
  ``python -m pytest tests/operations/test_issue494_contract_resolvers_offline.py -m "not requires_live_project" -q``
- Live: **N/A** (docstring-only)
- Evidence: ``specs/494-contract-resolvers/evidence/offline-494.md``
