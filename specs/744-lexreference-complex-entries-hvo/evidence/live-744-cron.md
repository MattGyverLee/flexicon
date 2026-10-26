# Issue #744 -- live evidence (cron)

**Command (not run on cloud agent):**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue744_lexreference_complex_entries_hvo_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified — no `clr` / FieldWorks on cloud cron host.

**run_mode:** n/a (live gate module present for merge host)
