# Issue #696 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue696_etymology_reorder_hvo_live.py -m requires_live_project -q
```

**run_mode:** not live (FLEx init failed: `No module named 'clr'` on cloud agent)

**Pre/post LCM readback:** not performed

**Result:** FAIL: unverified (blocker: no FieldWorks/pythonnet on this VM)
