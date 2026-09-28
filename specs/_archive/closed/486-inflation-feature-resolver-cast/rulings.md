# Issue #486 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #486 (P3) -- InflectionFeatureOperations HVO resolvers uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none**
- Open **P3** bugs without an open PR: **#486** (filed this run; promoted from #284)
- Did not select **#459** (fix merged as PR #460; issue still open -- close separately)
- Did not select **#284** (re-triage tracking, not a defect report)

## RULING (binding)

Cast all four private resolvers through `cast_to_concrete` on every path:

- `__ResolveInflectionClass` -- callers read `IMoInflClass.Name` (e.g. lines 337, 379).
- `__ResolveFeatureStructure` -- callers use `_GetTypedOwner(fs)` on delete path.
- `__ResolveFeature` -- callers duck-type via `hasattr(feature, "ValuesOC")` (silent loss).
- `__ResolveFeatureSystem` -- callers duck-type via `hasattr(feature_system, "TypesOC")`.

Do **not** add a ClassName guard that returns uncast objects on miss; match the
#459 / #455 / #268 family.

## Verification plan

- Offline: `tests/operations/test_issue486_inflation_feature_resolver_cast_offline.py`
- Live: `target_sandbox` gate calling `InflectionClassGetName(ic_hvo)` only
  (`requires_live_project`).
