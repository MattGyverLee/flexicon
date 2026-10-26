# Issue #718 offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue718_lexsense_semanticdomain_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** PASS (3/3)

**run_mode:** mock (cloud agent; no live LCM session)

**Pre-state:** `AddSemanticDomain` / `RemoveSemanticDomain` used `domain in sense.SemanticDomainsRC`.

**Post-state (source ratchet):** Both methods compare `Hvo` when testing membership and when removing.
