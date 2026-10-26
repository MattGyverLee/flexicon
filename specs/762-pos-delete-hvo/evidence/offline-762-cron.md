# Issue #762 offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue762_pos_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** offline (cloud agent)

**Result:** PASS (3 passed, cron cloud agent 2026-10-25)
