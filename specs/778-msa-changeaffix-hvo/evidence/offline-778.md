# Issue #778 -- offline evidence

**Command:**

```
python3 -m pytest tests/operations/test_issue778_msa_changeaffix_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks)

**Result:** (filled after pytest run)

**Live LCM:** FAIL: unverified -- no FieldWorks / pythonnet clr in cloud environment.
