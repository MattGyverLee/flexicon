# Issue #502 offline verification (cron cloud)

**Command:**

```bash
python3 -m pytest \
  tests/operations/test_issue502_wfigloss_analysis_resolver_cast_offline.py \
  -m "not requires_live_project" -q
```

**Result:** PASS (2/2)

**Date:** 2026-09-25
