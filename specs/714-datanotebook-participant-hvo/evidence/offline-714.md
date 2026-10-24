# Issue #714 -- offline evidence

**Command:**

```
python3 -m pytest tests/operations/test_issue714_datanotebook_participant_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** mock (no live LCM in cloud agent)

**Result:** PASS (see pytest output at commit time)

**Live:** FAIL: unverified (no clr / FieldWorks on cloud agent)
