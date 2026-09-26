# Offline evidence -- issue #535 (cron)

**Command:**

```
python3 -m pytest -m "not requires_live_project" tests/operations/test_issue535_naturalclass_duplicate_hvo_offline.py -q
```

**Result:** PASS 2/2

**run_mode:** N/A (static source ratchet; `tests/live_status.json` not updated)
