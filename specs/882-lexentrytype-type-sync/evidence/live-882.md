# Issue #882 live verification

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue882_lexentrytype_type_sync_live.py -m requires_live_project -q
```

**run_mode:** mock (cloud agent, no FieldWorks/clr)

**Result:** FAIL: unverified

**Pre/post LCM read-back:** not performed (environment lacks live LCM)
