# Issue #768 offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue768_variant_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** offline (cloud agent)

**Result:** PASS (cron cloud agent 2026-10-25)
