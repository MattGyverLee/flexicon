# Issue #720 offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue720_lexsense_usagetype_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** (filled at commit time)

**run_mode:** mock (cloud agent; no live LCM session)

**Pre-state:** `AddUsageType` / `RemoveUsageType` used `usage_type in sense.UsageTypesRC`.

**Post-state (source ratchet):** Both methods compare `Hvo` when testing membership and when removing.
