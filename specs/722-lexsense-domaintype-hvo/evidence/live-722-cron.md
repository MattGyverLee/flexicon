# Issue #722 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue722_lexsense_domaintype_hvo_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified (cloud agent has no FieldWorks / clr)

**run_mode:** not executed on this host

**Expected live check:** Add domain type to sense, re-fetch via `project.Object(hvo)`, `RemoveDomainType` must clear the link.
