# Live evidence -- issue #848

**Command:**

```bash
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue848_infl_deletevalue_hvo_live.py -m requires_live_project -q
```

**run_mode:** mock (no `clr` / FieldWorks on cloud agent)

**Pre-state:** N/A (live session did not start)

**Post-state:** N/A

**Result:** FAIL: unverified -- live LCM write-path proof not performed in this environment.
