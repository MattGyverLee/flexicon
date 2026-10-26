# Issue #726 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue726_lexsense_donotpublish_hvo_live.py -m requires_live_project -q
```

**run_mode:** mock (FLEx init failed before any project open)

**Blocker:** Cloud agent VM has no FieldWorks / .NET runtime (`pythonnet` cannot create default runtime).

**Result:** **FAIL: unverified** -- live gate module is present; human or Windows loop clone must run the live file with `FLEXLIBS_REQUIRE_LIVE=1` before merge.

**Expected pass criterion:** After `AddDoNotPublishIn(sense, publication)`, `RemoveDoNotPublishIn(sense, project.Object(publication.Hvo))` leaves `GetDoNotPublishIn(sense)` empty (read back from LCM via ops, not the object passed in).
