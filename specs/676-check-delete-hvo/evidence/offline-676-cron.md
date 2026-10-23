# Issue #676 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue676_check_delete_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (cloud agent; no live LCM)

**Result:** PASS (2/2 offline ratchet tests)

**Live LCM:** FAIL: unverified — no FieldWorks/pythonnet (`clr`) on cloud VM.
