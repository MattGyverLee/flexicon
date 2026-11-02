# Issue #850 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/850-infl-createvalue-except from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (recent HVO/sync issues #833–#848 each have merged PRs)
- Open **P3** bugs without an open PR: **none**
- **#776** / **#826** remain open but fixes already landed on main via PR #827; no unfixed code path selected.
- Selected **P2 #850** (new): `InflectionFeatureOperations.CreateValue` bare `except Exception` on the `IFsClosedFeature` cast -- sibling gap from #848 lex-lead out-of-scope note (complex-feature value surfaces).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Restrict the cast guard on `IFsClosedFeature(feature)` to invalid-owner failures only (`AttributeError`, `System.InvalidCastException`); map those to the existing `FP_ParameterError` message for complex/non-closed features.
2. Do not wrap the ValuesOC mutation block in a bare `except Exception`.
3. Tag the cast guard with `issue #850` in comments.
4. Do not refactor unrelated InflectionFeatureOperations paths in this PR.

**Out of scope:** PhonFeatureOperations (no equivalent cast guard); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue850_infl_createvalue_except_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue850_infl_createvalue_except_live.py -m requires_live_project -q` on `target_sandbox`.
