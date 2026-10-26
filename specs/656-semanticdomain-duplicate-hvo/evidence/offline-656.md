# Issue #656 -- offline verification evidence

**Command:**

```
python3 -m pytest -m "not requires_live_project" tests/operations/test_issue656_semanticdomain_duplicate_hvo_offline.py -q
```

**Result:** PASS (2 passed)

**run_mode:** mock (default cloud agent; no FieldWorks LCM)
