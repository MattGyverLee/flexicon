# Issue #788 offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue788_paragraph_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks)

**Result:** PASS (2/2)

**Date:** 2026-10-25
