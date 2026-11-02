# Issue #846 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/846-featurestructure-delete-hvo from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs #833, #834, #836, #840, #842, #844 each have open PRs (#837–#839, #841, #843, #845).
- Open **P3** bugs without an open PR: **none**
- **#776** / **#826** remain open but fixes already landed on main via PR #827; no unfixed code path selected.
- Selected **P2 #846** (new): `InflectionFeatureOperations.FeatureStructureDelete` uses `parent.FeaturesOA == fs` proxy identity -- sibling gap from #840 lex-lead out-of-scope note (other InflectionFeatureOperations write paths).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. After `_GetTypedOwner(fs)`, treat the slot as matching when `parent.FeaturesOA` is non-null and its `Hvo` equals the resolved structure's `Hvo`; do not use `==` on the handles.
2. Clear `parent.FeaturesOA` inside the existing transaction bracket when the HVOs match.
3. Tag the slot check with `issue #846` in comments.
4. Do not refactor unrelated InflectionFeatureOperations paths in this PR.

**Out of scope:** Owners whose feature-structure slot is not named `FeaturesOA` (C1 resolver work); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue846_featurestructure_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue846_featurestructure_delete_hvo_live.py -m requires_live_project -q` on `target_project`.
