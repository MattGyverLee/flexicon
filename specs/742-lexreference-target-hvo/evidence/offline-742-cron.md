# Issue #742 -- offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue742_lexreference_target_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no live LCM)

**Result:** PASS (3/3 offline ratchet tests)

**Live LCM:** FAIL: unverified — no FieldWorks/pythonnet (`clr`) on cloud VM.
