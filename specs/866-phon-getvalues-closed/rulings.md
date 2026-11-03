# Issue #866 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/866-phon-getvalues-closed from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#864 each have open PRs #853–#865)
- Open **P3** bugs without an open PR: **none**
- **#776** / **#826** remain open but fixes already landed on main via PR #827; no unfixed code path selected.
- Selected **P2 #866** (new): `PhonFeatureOperations.GetValues` iterates `ValuesOC` without `IFsClosedFeature` validation -- sibling gap from **#852** lex-lead scope (CreateValue write guard landed in PR **#853**; read path `GetValues` was not in that PR).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Cast resolved feature to `IFsClosedFeature` before the `ValuesOC` iteration; map invalid-owner cast failures (`AttributeError`, `System.InvalidCastException`) to `FP_ParameterError` with the same closed-feature message shape as **#852** CreateValue (wording adjusted to `GetValues requires...`).
2. Do not wrap the cast guard or iteration block in bare `except Exception`.
3. Tag the cast guard with `issue #866` in comments.
4. Do not refactor unrelated PhonFeatureOperations paths or inflection `FeatureGetValues` in this PR.

**Out of scope:** Inflection `FeatureGetValues` parity (separate issue if filed); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue866_phon_getvalues_closed_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue866_phon_getvalues_closed_live.py -m requires_live_project -q` on `target_sandbox`.
