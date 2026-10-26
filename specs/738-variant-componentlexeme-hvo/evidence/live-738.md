# Issue #738 live evidence

**Command:**

```
cd /workspace/.worktrees/fix-738-variant-componentlexeme-hvo
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue738_variant_componentlexeme_hvo_live.py -m requires_live_project -q
```

**Result:** 2 errors at collection/setup (FLEx init failed: no .NET runtime / pythonnet `clr` unavailable on cloud agent)

**run_mode:** not live (session refused mock fallback due to `FLEXLIBS_REQUIRE_LIVE=1`)

**Pass/fail:** FAIL: unverified (no clr / FieldWorks on this host)

**Pre-state / post-state LCM readback:** not performed (blocked at init)
