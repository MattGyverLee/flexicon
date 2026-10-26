# Issue #762 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue762_pos_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (cloud agent; no clr / FieldWorks)

**Expected on Windows with FieldWorks:** `Delete` and `RemoveSubcategory` detach when passing `Object(hvo)` after create.
