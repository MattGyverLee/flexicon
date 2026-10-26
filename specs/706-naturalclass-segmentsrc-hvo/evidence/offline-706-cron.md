# Issue #706 -- offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue706_naturalclass_segmentsrc_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks)

**Result:** PASS (3/3, 2026-10-24 cron cloud agent)
