# Offline evidence -- issue #513 (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue513_discourse_owner_cast_offline.py -m "not requires_live_project" -q
```

**Result:** 4 passed

**run_mode:** N/A (offline)

**Pre/post LCM:** N/A

**Pass/fail:** PASS (offline ratchet)
