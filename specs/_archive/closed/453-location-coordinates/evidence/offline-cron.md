# Issue #453 -- offline evidence (cron)

**Date:** 2026-09-24  
**Branch:** `fix/453-location-coordinates`

## Command

```
python3 -m pytest tests/operations/test_issue453_location_coordinates_offline.py -q
```

## Result

PASS (4 tests).

## Live

**FAIL: unverified** -- cloud agent host has no FieldWorks runtime (`run_mode` not live).
