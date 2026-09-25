# Issue #470 -- offline verification evidence

**Command:**

```bash
python3 -m pytest tests/operations/test_issue470_reorder_clear_offline.py -m "not requires_live_project" -q
```

**Result:** PASS 12/12 (cloud cron 2026-09-25)

**run_mode:** mock (no FieldWorks on host; tests avoid flexicon import)
