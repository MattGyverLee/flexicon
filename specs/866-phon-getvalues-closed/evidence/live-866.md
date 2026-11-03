# Issue #866 live verification

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue866_phon_getvalues_closed_live.py -m requires_live_project -q
```

**run_mode:** mock (cloud agent — no FieldWorks/CLR)

**Pre-state:** N/A (live project unavailable)

**Post-state:** N/A

**Result:** FAIL: unverified — live LCM not available in this environment.
