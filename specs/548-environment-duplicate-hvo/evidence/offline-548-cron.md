# Issue #548 -- offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue548_environment_duplicate_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (offline ratchet only)

**Result:** PASS (2/2)

**Notes:** Cloud agent has no FieldWorks/clr; live gate not executed here.
