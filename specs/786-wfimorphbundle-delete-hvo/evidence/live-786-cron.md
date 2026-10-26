# Issue #786 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue786_wfimorphbundle_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified — no `clr` / FieldWorks on cloud agent (`tests/live_status.json` would remain `mock`).

**Blocker:** Live LCM verification requires Windows loop clone with FieldWorks 9+.

**Date:** 2026-10-25
