# Issue #870 live verification

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue870_phon_applyvalues_closed_live.py -m requires_live_project -q
```

**run_mode:** mock (cloud agent -- no FieldWorks/CLR)

**Pre-state:** N/A (live project unavailable)

**Post-state:** N/A

**Result:** FAIL: unverified -- live LCM not available in this environment.
