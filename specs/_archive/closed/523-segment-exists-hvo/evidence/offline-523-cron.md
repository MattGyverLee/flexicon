# Issue #523 -- offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue523_segment_exists_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (offline gate only)

**Result:** 2 passed in 0.06s
