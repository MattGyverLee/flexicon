# Offline evidence -- #457 LexSenseOperations resolver cast

**Date:** 2026-09-24

## Command

```
python3 -m pytest tests/operations/test_issue457_lexsense_resolver_cast_offline.py -m "not requires_live_project" -q
```

## Result

`[PASS]` offline ratchet 2/2 (`python3 -m pytest ... -q`).

## Live

`[FAIL: unverified]` -- cloud agent environment has no FieldWorks / LCM;
`FLEXLIBS_REQUIRE_LIVE=1` live gate not executed here.
