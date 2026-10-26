# Issue #670 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue670_split_segment_hvo_live.py -m requires_live_project -q
```

**run_mode:** mock (FLEx init failed: `No module named 'clr'`)

**Result:** ERROR at collection/setup -- live gate not executed

**Pass/fail:** FAIL: unverified (no LCM on this host)
