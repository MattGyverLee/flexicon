# Issue #833 offline evidence

**Command:**

```
python3 -m pytest tests/operations/test_issue833_check_getlist_offline.py -m "not requires_live_project" -q
```

**run_mode:** N/A (offline ratchet; no live_status.json)

**Result:** PASS (4 tests) — re-run 2026-11-02 cron

**Live:** FAIL: unverified (no clr / FieldWorks in cloud agent)
