# Issue #642 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue642_etymology_duplicate_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** 2 passed

**Live LCM:** FAIL: unverified (no clr / FieldWorks on cloud agent VM)

**run_mode:** mock (no live_status.json write from live run)
