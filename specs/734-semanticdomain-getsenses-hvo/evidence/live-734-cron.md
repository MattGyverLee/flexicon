# Issue #734 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue734_semanticdomain_getsenses_hvo_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified (cloud agent has no FieldWorks / clr)

**run_mode:** not executed on this host

**Expected live check:** Add domain to sense, re-fetch domain via `project.Object(hvo)`, `GetSensesInDomain` must include the sense.
