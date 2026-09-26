# Offline evidence -- issue #531 (cron)

**Command:**

```
python3 -m pytest -m "not requires_live_project" tests/operations/test_issue531_paragraph_duplicate_hvo_offline.py -q
```

**Result:** PASS (cloud agent, 2026-09-26)

**run_mode:** mock (offline ratchet only)
