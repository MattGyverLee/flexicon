# Issue #808 offline evidence

**Command:**

```
python -m pytest tests/operations/test_issue808_pronunciation_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** offline (no `tests/live_status.json` live gate for this module)

**Result:** PASS (recorded at commit time in cloud agent)
