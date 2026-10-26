# Issue #770 offline evidence

**Command:**

```
python3 -m pytest tests/operations/test_issue770_msa_exception_feature_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** PASS (recorded at commit time by cron automation)

**run_mode:** mock (offline ratchet only)
