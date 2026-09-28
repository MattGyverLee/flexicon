# Issue #525 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue525_merge_segments_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (cloud agent -- no FieldWorks / pythonnet `clr` on PATH)

**Pre-state / post-state:** Not exercised on live LCM.

**Pass/fail:** FAIL: unverified (live)
