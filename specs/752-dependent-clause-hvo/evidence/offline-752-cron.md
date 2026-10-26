# Issue #752 offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue752_dependent_clause_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** offline (no live_status.json write)

**Result:** PASS 2/2 (cron cloud agent, 2026-10-25)
