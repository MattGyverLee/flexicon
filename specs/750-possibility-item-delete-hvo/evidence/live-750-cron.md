# Issue #750 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue750_possibility_item_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (cloud agent; no clr / FieldWorks)

**Result:** Live gate module present; execution blocked on this environment.
