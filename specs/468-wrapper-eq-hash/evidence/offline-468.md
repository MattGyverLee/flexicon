# Issue #468 -- offline evidence

**Command:**

```
python -m pytest tests/operations/test_issue468_wrapper_eq_hash_offline.py -m "not requires_live_project" -q
```

**run_mode:** N/A (offline-only change; no LCM write path)

**Result:** PASS (see pytest output in PR)
