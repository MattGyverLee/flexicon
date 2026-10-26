# Issue #804 -- offline evidence

**Command:**

```
python -m pytest tests/operations/test_issue804_lexsense_delete_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** PASS (recorded at commit time in cloud agent)

**run_mode:** mock (offline ratchet only)
