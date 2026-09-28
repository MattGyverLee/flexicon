# Issue #473 -- live evidence

**Status:** FAIL: unverified (no FLEx / libmono on cloud agent)

**Command (not run to completion):**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue473_scripture_discourse_move_live.py -m requires_live_project -q
```

**run_mode:** n/a (live suite not added; gate deferred to Windows/FieldWorks host)
