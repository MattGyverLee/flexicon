# Live verification -- issue #510 (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue510_discourse_chart_row_resolver_live.py -m requires_live_project -q
```

**run_mode:** mock (FLEx init failed: `No module named 'clr'`)

**Result:** FAIL: unverified

**Blocker:** Cloud agent environment has no pythonnet / FieldWorks LCM stack.

**Date:** 2026-09-25
