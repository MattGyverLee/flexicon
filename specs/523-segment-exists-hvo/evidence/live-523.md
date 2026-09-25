# Issue #523 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue523_segment_exists_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (cloud agent — no FieldWorks / pythonnet `clr` on PATH)

**Pre-state / post-state:** Not exercised on live LCM.

**Offline gate:** PASS — `python3 -m pytest tests/operations/test_issue523_segment_exists_hvo_offline.py -m "not requires_live_project" -q` → 2 passed.

**Pass/fail:** FAIL: unverified (live); PASS (offline ratchet)
