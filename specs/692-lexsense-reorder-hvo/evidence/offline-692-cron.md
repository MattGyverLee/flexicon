# Issue #692 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue692_lexsense_reorder_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks)

**Result:** PASS (3/3, 2026-10-23 cron cloud agent)
