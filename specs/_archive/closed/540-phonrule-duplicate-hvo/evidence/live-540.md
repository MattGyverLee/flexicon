# Issue #540 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue540_phonrule_duplicate_hvo_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified (cloud agent has no clr / FieldWorks)

**run_mode:** mock (no live LCM on this runner)

**Pass/fail:** FAIL: unverified -- write-path change requires live read-back; not performed here.
