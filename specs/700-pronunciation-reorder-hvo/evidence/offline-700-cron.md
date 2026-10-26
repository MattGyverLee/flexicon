# Issue #700 -- offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue700_pronunciation_reorder_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** PASS (3/3)

**run_mode:** mock (offline ratchet only; no LCM write path executed)

**Pass/fail:** PASS offline gate for #700 HVO partition ratchet.
