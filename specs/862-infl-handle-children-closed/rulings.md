# Issue #862 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/862-infl-handle-children-closed from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#860 each have open PRs #853–#861)
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #862** (new): `InflectionFeatureOperations._handle_entry_children` reads `ValuesOC` without `IFsClosedFeature` validation -- sibling gap from #858 lex-lead out-of-scope note (catalog child-import entry, not `_CreateValueFromEntry` factory).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Cast `created_feature` to `IFsClosedFeature` before the `ValuesOC` idempotency scan; map invalid-owner cast failures (`AttributeError`, `System.InvalidCastException`) to `FP_ParameterError` with the same closed-feature message shape as **#850** / **#858** / phonology **#856**.
2. Do not wrap the cast or scan block in bare `except Exception`.
3. Tag the cast guard with `issue #862` in comments.
4. Do not refactor unrelated InflectionFeatureOperations paths or phonology `_handle_entry_children` in this PR.

**Out of scope:** PhonFeatureOperations catalog `_handle_entry_children` parity; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue862_infl_handle_children_closed_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue862_infl_handle_children_closed_live.py -m requires_live_project -q` on `target_sandbox`.
