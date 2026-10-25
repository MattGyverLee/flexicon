# Issue #746 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue746_phoneme_removecode_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks)

**Result:** PASS (3/3, 2026-10-25 cron cloud agent)
