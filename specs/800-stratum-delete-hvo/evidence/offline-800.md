# Issue #800 -- offline evidence

**Command:**

```
python -m pytest tests/operations/test_issue800_stratum_delete_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** 2 passed

**run_mode:** mock (offline ratchet only; `tests/live_status.json` not live)
