# Issue #776 -- offline verification evidence

**Command:**

```bash
python3 -m pytest tests/operations/test_issue776_baseops_sort_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** offline (cloud agent; no `tests/live_status.json` update)

**Result:** PASS (3 tests)

**Live LCM:** FAIL: unverified -- no FieldWorks / pythonnet clr in cloud environment.
