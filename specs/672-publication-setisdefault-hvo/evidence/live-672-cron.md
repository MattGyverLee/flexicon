# Issue #672 -- live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue672_publication_setisdefault_hvo_live.py -m requires_live_project -q
```

**run_mode:** not executed on cloud VM (no `clr`)

**Result:** FAIL: unverified

**Blocker:** Cloud agent environment lacks FieldWorks / pythonnet live LCM.
