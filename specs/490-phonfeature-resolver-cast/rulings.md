# Issue #490 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #490 (P3) -- PhonFeatureOperations `__ResolveObject` uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none**
- Open **P3** bugs without an open PR: **#284** (re-triage tracking only)
- **Filed and selected #490** this run from the #284 inventory
  (`__ResolveObject` at `PhonFeatureOperations.py:1088`; callers read `Name` at
  :175, `ValuesOC` at :222)

## RULING (binding)

Cast `__ResolveObject` through `cast_to_concrete` on every path. Match the
#488 / #459 / #268 family. Do not return uncast objects on the HVO path.

## Verification plan

- Offline: `tests/operations/test_issue490_phonfeature_resolver_cast_offline.py`
- Live: `target_sandbox` gate calling `GetName(feature_hvo)` with a genuine
  feature HVO only (`requires_live_project`).
