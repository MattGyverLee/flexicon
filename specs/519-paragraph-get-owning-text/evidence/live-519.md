# Live evidence -- issue #519 (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue519_paragraph_get_owning_text_live.py -m requires_live_project -q
```

**Result:** ERROR -- `No module named 'clr'` (no FieldWorks / pythonnet in cloud agent)

**run_mode:** mock (session refused live; FLEXLIBS_REQUIRE_LIVE=1 raised UsageError)

**Pre/post LCM:** not exercised

**Pass/fail:** FAIL: unverified
