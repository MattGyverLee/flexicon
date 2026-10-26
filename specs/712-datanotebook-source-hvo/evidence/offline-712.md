# Issue #712 offline evidence

**Command:**

```
python -m pytest tests/operations/test_issue712_datanotebook_source_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** 3 passed

**run_mode:** mock (cloud agent; no FLEx/clr)

**Live LCM:** FAIL: unverified (no clr on this VM)
