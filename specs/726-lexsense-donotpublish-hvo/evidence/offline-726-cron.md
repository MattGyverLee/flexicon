# Issue #726 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue726_lexsense_donotpublish_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** PASS (3 passed)

**run_mode:** N/A (offline ratchet only)
