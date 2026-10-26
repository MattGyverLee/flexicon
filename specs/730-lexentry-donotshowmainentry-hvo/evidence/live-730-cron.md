# Issue #730 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue730_lexentry_donotshowmainentry_hvo_live.py -m requires_live_project -q
```

**run_mode:** not recorded (session aborted before live_status write -- no `clr` on cloud agent)

**Result:** FAIL: unverified -- `pytest.UsageError: FLEXLIBS_REQUIRE_LIVE=1 set but FLEx initialization failed: No module named 'clr'`
