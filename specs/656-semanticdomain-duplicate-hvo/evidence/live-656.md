# Issue #656 -- live verification evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue656_semanticdomain_duplicate_hvo_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified -- `ModuleNotFoundError: No module named 'clr'` (no FieldWorks / pythonnet on this cloud agent)

**run_mode:** not live (tests/live_status.json would report mock if collection ran)

**Pass/fail line:** FAIL: unverified (blocker: no LCM)
