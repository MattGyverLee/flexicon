# Issue #820 -- lex-lead ruling

**Date:** 2026-10-26  
**HEAD:** fix/820-inflfeature-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR (#640 has PR #641; cursor-filed HVO sweep issues each have open PRs).
- Selected **P2 #820** (new): `InflectionFeatureOperations.FeatureDelete` bare-proxy `MsFeatureSystemOA.FeaturesOC` `.Remove` -- sibling gap named in #818 lex-lead ruling.

## RULING (binding)

`InflectionFeatureOperations.FeatureDelete` must resolve collection membership by **HVO** before mutating, matching #816 PhonFeature Delete / #818 DataNotebook Delete.

**Fix for this PR:**

1. Scan `MsFeatureSystemOA.FeaturesOC` for a slot whose `Hvo` matches the resolved feature; `Remove` the matched member.
2. Raise `FP_ParameterError` if no member found.
3. Offline source ratchet + live gate module under `tests/operations/test_issue820_*`.

**Out of scope:** `InflectionClassDelete` bare `SubclassesOC`/`InflectionClassesOC` `.Remove` (file as next sibling); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

**Next sibling (file after merge):** `InflectionFeatureOperations.InflectionClassDelete` bare owning-sequence `.Remove` (no open issue at filing time).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue820_inflfeature_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue820_inflfeature_delete_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
