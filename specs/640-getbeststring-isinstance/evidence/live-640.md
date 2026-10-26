# Issue #640 live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue640_getbeststring_live.py -m requires_live_project -q
```

**run_mode:** mock (FLEx init failed; `tests/live_status.json` not live)

**Blocker:** Cloud VM has no .NET/FieldWorks runtime (`Failed to create a default .NET runtime`).

**Result:** FAIL: unverified -- live gate module present; LCM read-back not executed on this host.

**Expected live check:** `GetBestString(sense.Gloss)` equals direct `BestAnalysisVernacularAlternative.Text` on Sena 3 sandbox.
