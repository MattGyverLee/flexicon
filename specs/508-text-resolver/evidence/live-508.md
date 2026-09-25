# Issue #508 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue508_text_resolver_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified -- cloud agent environment has no FieldWorks / LCM stack (`pytest` installed ad hoc; live plugin cannot open Target).

**run_mode:** not live (no `tests/live_status.json` with `"run_mode": "live"`)

**Pre/post LCM read-back:** not performed.
