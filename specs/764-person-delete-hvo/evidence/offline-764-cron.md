# Issue #764 offline evidence (cron)

**Command:**

```
python3 -m pytest -m "not requires_live_project" tests/operations/test_issue764_person_delete_hvo_offline.py -q
```

**Result:** PASS (2/2)

**run_mode:** mock (cloud agent; no FieldWorks CLR)
