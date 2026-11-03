# Issue #870 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/870-phon-applyvalues-closed from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#868 each have open PRs #853–#869)
- Open **P3** bugs without an open PR: **none**
- **#776** / **#826** / **#850** remain open but fixes already landed on main via PR **#827** / **#851**; no unfixed code path selected.
- Selected **P2 #870** (new): `PhonFeatureOperations.__ApplyValues` reads `ValuesOC` without invalid-owner mapping on the internal re-resolve -- sibling gap from **#868** lex-lead out-of-scope note (closed-feature value surfaces beyond **#866** / **#854** apply entry).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Cast resolved feature to `IFsClosedFeature` inside `__ApplyValues` before the `ValuesOC` GUID index build; map invalid-owner cast failures (`AttributeError`, `System.InvalidCastException`) to `FP_ParameterError` with the same closed-feature message shape as **#852** / **#854** (wording adjusted to `__ApplyValues requires...`).
2. Do not wrap the cast guard or enumeration block in bare `except Exception`.
3. Tag the cast guard with `issue #870` in comments.
4. Do not refactor unrelated PhonFeatureOperations paths or the public `ApplySyncableProperties` entry guard (**#854** / PR **#855**) in this PR.

**Out of scope:** Inflection feature sync (no `ValuesOC` apply path on that class); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue870_phon_applyvalues_closed_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue870_phon_applyvalues_closed_live.py -m requires_live_project -q` on `target_sandbox`.
