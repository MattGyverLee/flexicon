# Issue #852 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/852-phon-createvalue-closed from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#850** fix merged (#851) but issue left open; no other labeled P2 on file.
- Open **P3** bugs without an open PR: **none**
- **#776** / **#826** remain open but fixes already landed on main via PR #827; no unfixed code path selected.
- Selected **P2 #852** (new): `PhonFeatureOperations.CreateValue` calls `ValuesOC.Add` without `IFsClosedFeature` validation -- sibling gap from #850 lex-lead out-of-scope note (phonology cast guard parity).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Cast resolved feature to `IFsClosedFeature` before `ValuesOC` mutation; map invalid-owner cast failures (`AttributeError`, `System.InvalidCastException`) to `FP_ParameterError` with the same closed-feature message shape as inflection #850.
2. Do not wrap the cast or factory block in bare `except Exception`.
3. Tag the cast guard with `issue #852` in comments.
4. Do not refactor unrelated PhonFeatureOperations paths in this PR.

**Out of scope:** Catalog `_CreateValueFromEntry` factory paths; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue852_phon_createvalue_closed_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue852_phon_createvalue_closed_live.py -m requires_live_project -q` on `target_sandbox`.
