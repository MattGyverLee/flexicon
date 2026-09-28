# Offline evidence -- #455 ExampleOperations resolver cast

**Date:** 2026-09-24

## Command

```
python3 -m pytest tests/operations/test_issue455_example_resolver_cast_offline.py -m "not requires_live_project" -q
python3 -m pytest -m "not requires_live_project" -q
```

## Result

`[PASS]` offline ratchet 2/2; full offline gate green (session recorded in
`tests/test_results.json`).

## Live

`[FAIL: unverified]` -- cloud agent environment has no FieldWorks / LCM;
`FLEXLIBS_REQUIRE_LIVE=1` live gate not executed here.
