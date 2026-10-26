# Issue #720 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue720_lexsense_usagetype_hvo_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified (cloud agent has no FieldWorks / clr)

**run_mode:** not executed on this host

**Expected live check:** Add usage type to sense, re-fetch via `project.Object(hvo)`, `RemoveUsageType` must clear the link.
