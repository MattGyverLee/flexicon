# Issue #858 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/858-infl-createvaluefromentry-closed from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** before filing; phonology **#852** / **#854** / **#856** each have open PRs **#853** / **#855** / **#857**; **#850** / **#776** / **#826** slices already on main.
- Filed **P2 #858** (new): `InflectionFeatureOperations._CreateValueFromEntry` uses `ValuesOC` without `IFsClosedFeature` validation -- sibling gap from **#856** lex-lead out-of-scope note (inflection catalog factory path).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Cast `parent_feature` to `IFsClosedFeature` before factory / `ValuesOC.Add`; map invalid-owner cast failures (`AttributeError`, `System.InvalidCastException`) to `FP_ParameterError` with the same closed-feature message shape as **#850** / phonology **#856**.
2. Do not wrap the cast or factory block in bare `except Exception`.
3. Tag the cast guard with `issue #858` in comments.
4. Do not refactor unrelated InflectionFeatureOperations paths or phonology `_CreateValueFromEntry` in this PR.

**Out of scope:** PhonFeatureOperations catalog parity (PR #857); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue858_infl_createvaluefromentry_closed_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue858_infl_createvaluefromentry_closed_live.py -m requires_live_project -q` on `target_sandbox`.
