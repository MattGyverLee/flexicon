# Issue #764 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue764_person_delete_hvo_live.py -m requires_live_project -q
```

**Result:** FAIL: unverified — no pythonnet/clr on cloud agent VM.

**run_mode:** not live (FieldWorks unavailable)

**Note:** Live gate module present; requires Windows FieldWorks host per CLAUDE.md.
