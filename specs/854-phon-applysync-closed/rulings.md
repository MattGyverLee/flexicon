# Issue #854 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/854-phon-applysync-closed from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#850** / **#776** / **#826** fixes on main (PRs #851 / #827); **#852** has open PR #853.
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #854** (new): `PhonFeatureOperations.ApplySyncableProperties` casts to `IFsClosedFeature` without invalid-owner mapping -- sibling gap from #852 lex-lead out-of-scope note (sync apply entry, not CreateValue).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Cast resolved feature to `IFsClosedFeature` before scalar/value sync; map invalid-owner cast failures (`AttributeError`, `System.InvalidCastException`) to `FP_ParameterError` with the same closed-feature message shape as inflection **#850** / phonology **#852**.
2. Do not wrap the cast or apply block in bare `except Exception`.
3. Tag the cast guard with `issue #854` in comments.
4. Do not refactor unrelated PhonFeatureOperations paths in this PR.

**Out of scope:** `__CreateValueFromEntry` catalog factory paths; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue854_phon_applysync_closed_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue854_phon_applysync_closed_live.py -m requires_live_project -q` on `target_sandbox`.
