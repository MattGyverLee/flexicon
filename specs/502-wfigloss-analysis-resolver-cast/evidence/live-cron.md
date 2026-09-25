# Issue #502 live verification (cron cloud)

**Command:**

```bash
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest \
  tests/operations/test_issue502_wfigloss_analysis_resolver_cast_live.py \
  -m requires_live_project -q
```

**run_mode:** mock (no FieldWorks / `clr` on Cursor cloud Linux)

**Result:** FAIL: unverified

**Note:** Write-path change; live gate module exists and follows `target_sandbox`
template. Re-run on a FieldWorks host before merge.
