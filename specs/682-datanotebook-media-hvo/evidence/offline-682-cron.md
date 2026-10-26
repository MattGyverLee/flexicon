# Issue #682 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue682_datanotebook_media_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no FieldWorks/clr)

**Result:** PASS (3/3 offline ratchet tests)

**Live LCM:** FAIL: unverified (no clr on cloud agent)
