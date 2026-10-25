# Issue #756 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue756_location_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (cloud agent; no clr / FieldWorks)

**Expected on Windows with FieldWorks:** nested `Delete` detaches when passing `Object(hvo)` after `Create` with parent.
