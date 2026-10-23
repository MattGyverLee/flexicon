# Issue #670 -- offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue670_split_segment_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** 2 passed

**run_mode:** N/A (offline ratchet only)

**Pre-state (main):** `para.SegmentsOS.IndexOf(seg)` in `SplitSegment`

**Post-state (branch):** HVO loop with `issue #670` comment; no `IndexOf(seg)` in SplitSegment block

**Pass/fail:** PASS (offline)
