# Issue #868 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/868-infl-featuregetvalues-closed from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#866 each have open PRs #853–#867)
- Open **P3** bugs without an open PR: **none**
- **#776** / **#826** remain open but fixes already landed on main via PR #827; no unfixed code path selected.
- Selected **P2 #868** (new): `InflectionFeatureOperations.FeatureGetValues` reads `ValuesOC` without `IFsClosedFeature` validation -- sibling gap from **#866** lex-lead scope (phonology `GetValues` guard in PR **#867**; inflection read path was explicitly out of scope).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Cast resolved feature to `IFsClosedFeature` before reading `ValuesOC`; map invalid-owner cast failures (`AttributeError`, `System.InvalidCastException`) to `FP_ParameterError` with the same closed-feature message shape as **#850** CreateValue (wording adjusted to `FeatureGetValues requires...`).
2. Do not wrap the cast guard or collection read in bare `except Exception`.
3. Tag the cast guard with `issue #868` in comments.
4. Do not refactor unrelated InflectionFeatureOperations paths or phonology `GetValues` in this PR.

**Out of scope:** Further closed-feature value surfaces not enumerated in **#866**; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue868_infl_featuregetvalues_closed_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue868_infl_featuregetvalues_closed_live.py -m requires_live_project -q` on `target_sandbox`.
