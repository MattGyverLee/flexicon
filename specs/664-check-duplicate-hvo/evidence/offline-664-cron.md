# Issue #664 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue664_check_duplicate_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** PASS (2 passed)

**run_mode:** mock (cloud Linux agent; no FieldWorks)

**Live:** FAIL: unverified -- `clr`/FieldWorks not available on this runner.
