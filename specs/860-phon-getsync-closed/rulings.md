# Issue #860 -- lex-lead ruling

**Date:** 2026-11-03  
**HEAD:** fix/860-phon-getsync-closed from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#852–#858 each have open PRs #853–#859)
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #860** (new): `PhonFeatureOperations.GetSyncableProperties` casts to `IFsClosedFeature` without invalid-owner mapping -- sibling gap from #854 lex-lead out-of-scope note (sync **extract** entry, not ApplySyncableProperties apply).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Cast resolved feature to `IFsClosedFeature` before scalar/`ValuesOC` reads; map invalid-owner cast failures (`AttributeError`, `System.InvalidCastException`) to `FP_ParameterError` with the same closed-feature message shape as inflection **#850** / phonology **#852** / **#854**.
2. Do not wrap the cast or extraction block in bare `except Exception`.
3. Tag the cast guard with `issue #860` in comments.
4. Do not refactor unrelated PhonFeatureOperations paths in this PR.

**Out of scope:** Inflection feature sync (no feature-level GetSyncableProperties); catalog `_CreateValueFromEntry` (#856); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue860_phon_getsync_closed_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue860_phon_getsync_closed_live.py -m requires_live_project -q` on `target_sandbox`.
