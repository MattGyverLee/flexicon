# Issue #694 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue694_example_reorder_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks)

**Result:** PASS (3/3, 2026-10-24 cron cloud agent)
