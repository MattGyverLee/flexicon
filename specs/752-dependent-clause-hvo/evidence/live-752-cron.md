# Issue #752 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue752_dependent_clause_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (cloud agent; no clr / FieldWorks)

**Expected on Windows with FieldWorks:** idempotent second `AddDependentClause` when passing `Object(hvo)` after linking via direct marker reference.
