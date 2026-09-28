# Issue #550 -- offline evidence

**Date:** 2026-09-26  
**Branch:** `fix/550-lexsense-duplicate-hvo`

## Command

```
cd .worktrees/fix-550-lexsense-duplicate-hvo
python3 -m pytest tests/operations/test_issue550_lexsense_duplicate_hvo_offline.py -m "not requires_live_project" -q
```

## Result

**PASS** -- 2 passed

## Live

**FAIL: unverified** -- cloud agent has no .NET/FieldWorks runtime (`FLEXLIBS_REQUIRE_LIVE=1` raises in `tests/flex_plugin.py`). `tests/live_status.json` not `run_mode: live`.
