# Issue #716 -- offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue716_reversal_sense_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks/clr)

**Result:** PASS (3/3, 2026-10-24 cron cloud agent)

**Live LCM:** FAIL: unverified (no clr on cloud agent)
