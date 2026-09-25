# Issue #448 live evidence (cron)

**Command (required when FieldWorks available):**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue448_move_item_live.py -m requires_live_project -q
```

**Cloud agent (2026-09-24):** FieldWorks / libmono not available.  
**run_mode:** mock (from `tests/live_status.json` after offline-only run)  
**Result:** **FAIL: unverified**

**Pre-state / post-state:** not collected on this runner.
