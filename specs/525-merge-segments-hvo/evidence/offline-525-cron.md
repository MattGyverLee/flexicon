# Issue #525 -- offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue525_merge_segments_hvo_offline.py -m "not requires_live_project" -q
```

**run_mode:** offline (no live_status.json for this slice)

**Pass/fail:** PASS (pending run)
