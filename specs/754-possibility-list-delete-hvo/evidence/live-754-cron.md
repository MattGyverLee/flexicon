# Issue #754 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue754_possibility_list_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (cloud agent; no clr / FieldWorks)

**Expected on Windows with FieldWorks:** nested `DeleteItem` detaches when passing `Object(hvo)` after `CreateItem`.
