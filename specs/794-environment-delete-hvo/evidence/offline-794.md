# Issue #794 -- offline evidence

**Command:**

```
python3 -m pytest tests/operations/test_issue794_environment_delete_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** 2 passed

**run_mode:** mock (offline ratchet only; `tests/live_status.json` not live)
