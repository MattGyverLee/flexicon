# Issue #734 offline evidence (cron)

**Command:**

```
python -m pytest tests/operations/test_issue734_semanticdomain_getsenses_hvo_offline.py -m "not requires_live_project" -q
```

**Result:** PASS (2/2)

**run_mode:** mock (cloud agent; no live LCM session)

**Pre-state:** `GetSensesInDomain` used `domain in sense.SemanticDomainsRC`.

**Post-state (source ratchet):** Loop compares `d.Hvo == domain_hvo` for membership.
