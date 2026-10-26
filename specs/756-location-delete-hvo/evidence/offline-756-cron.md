# Issue #756 offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue756_location_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** offline (no live_status.json write)

**Result:** PASS (cron cloud agent, 2026-10-25)
