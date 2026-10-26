# Issue #766 offline evidence (cron)

**Command:**

```
python3 -m pytest -m "not requires_live_project" tests/operations/test_issue766_lexref_deletetype_hvo_offline.py -q
```

**Result:** PASS (2/2)

**run_mode:** mock (cloud agent; no FieldWorks CLR)
