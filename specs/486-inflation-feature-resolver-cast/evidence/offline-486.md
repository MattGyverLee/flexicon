# Offline evidence -- #486 InflectionFeatureOperations resolver cast

**Date:** 2026-09-25

## Command

```
python3 -m pytest tests/operations/test_issue486_inflation_feature_resolver_cast_offline.py -m "not requires_live_project" -q
```

## Result

`[PASS]` offline ratchet 2/2 (`tests/test_results.json` in worktree).

## Live

`[FAIL: unverified]` -- cloud agent environment has no FieldWorks / LCM;
`FLEXLIBS_REQUIRE_LIVE=1` live gate not executed here.
