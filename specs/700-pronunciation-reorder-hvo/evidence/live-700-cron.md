# Issue #700 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue700_pronunciation_reorder_hvo_live.py -m requires_live_project -q
```

**run_mode:** unverified (cloud agent has no FieldWorks / clr)

**Pre-state / post-state read back from LCM:** not performed

**Pass/fail:** FAIL: unverified -- live LCM verification blocked (no clr on this host)
