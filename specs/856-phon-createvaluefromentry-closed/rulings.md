# Issue #856 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/856-phon-createvaluefromentry-closed from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#850** / **#776** / **#826** fixes on main (PRs #851 / #827); **#852** / **#854** have open PRs #853 / #855.
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #856** (new): `PhonFeatureOperations._CreateValueFromEntry` uses `ValuesOC` without `IFsClosedFeature` validation -- sibling gap from #854 lex-lead out-of-scope note (catalog factory path).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Cast `parent_feature` to `IFsClosedFeature` before factory / `ValuesOC.Add`; map invalid-owner cast failures (`AttributeError`, `System.InvalidCastException`) to `FP_ParameterError` with the same closed-feature message shape as **#850** / **#852** / **#854**.
2. Do not wrap the cast or factory block in bare `except Exception`.
3. Tag the cast guard with `issue #856` in comments.
4. Do not refactor unrelated PhonFeatureOperations paths or inflection `_CreateValueFromEntry` in this PR.

**Out of scope:** InflectionFeatureOperations catalog parity; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue856_phon_createvaluefromentry_closed_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue856_phon_createvaluefromentry_closed_live.py -m requires_live_project -q` on `target_sandbox`.
