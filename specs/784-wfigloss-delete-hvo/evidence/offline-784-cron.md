# Issue #784 offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue784_wfigloss_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks)

**Result:** PASS (2/2)

**Date:** 2026-10-25
