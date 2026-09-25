# Offline evidence -- #459 PronunciationOperations resolver cast

**Date:** 2026-09-24

## Command

```
python3 -m pytest tests/operations/test_issue459_pronunciation_resolver_cast_offline.py -m "not requires_live_project" -q
```

## Result

`[PASS]` offline ratchet 2/2 (`tests/test_results.json` in worktree).

Full-repo `python3 -m pytest -m "not requires_live_project" -q` was **not**
executed in this cloud pod (no libmono / FieldWorks); collection errors on
import are expected here.

## Live

`[FAIL: unverified]` -- cloud agent environment has no FieldWorks / LCM;
`FLEXLIBS_REQUIRE_LIVE=1` live gate not executed here.
