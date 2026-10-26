# Issue #678 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue678_annotationdef_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks/clr)

**Result:** PASS (2/2 offline ratchet tests)

**Live LCM:** FAIL: unverified (no clr on cloud agent)
