# Issue #548 -- live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue548_environment_duplicate_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (no clr / FieldWorks on cloud agent)

**Pre-state:** N/A

**Post-state read back from LCM:** N/A

**Result:** Live verification must be run on a FieldWorks host before merge.
