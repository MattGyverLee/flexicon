# Live verification -- issue #834

**Command (required on Windows + FieldWorks):**

```
set FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_issue658_note_duplicate_hvo_live.py -m requires_live_project -q
```

**Expected:** PASS (behaviour unchanged from #658; duplicate still attaches under parent).

**Cloud agent run:** FAIL: unverified (no FieldWorks / pythonnet clr in this environment).

**run_mode:** mock (see `tests/live_status.json` after offline session)
