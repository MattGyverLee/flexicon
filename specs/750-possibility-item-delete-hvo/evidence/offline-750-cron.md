# Issue #750 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue750_possibility_item_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks)

**Result:** PASS (2/2, 2026-10-25 cron cloud agent)
