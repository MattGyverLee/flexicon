# Issue #722 offline evidence (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue722_lexsense_domaintype_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** 3 passed

**run_mode:** mock (cloud agent; no live LCM session)

**Pre-state:** `AddDomainType` / `RemoveDomainType` used `domain_type in sense.DomainTypesRC`.

**Post-state (source ratchet):** Both methods compare `Hvo` when testing membership and when removing.
