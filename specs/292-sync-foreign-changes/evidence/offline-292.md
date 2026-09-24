# Offline verification -- issue #292 SyncForeignChanges

**Date:** 2026-09-24  
**Branch:** fix/292-sync-foreign-changes  
**run_mode:** mock (cloud agent; no live LCM on this pod)

## Command

```
python -m pytest tests/operations/test_issue292_sync_foreign_changes_offline.py -m "not requires_live_project" -q
```

## Result

PASS: `2 passed, 6 skipped` (six guard-path tests skip when SIL.LCModel / pythonnet is unavailable on the pod; source ratchet + ruling doc tests always run).

## Live

**FAIL: unverified** -- two-session shared-mode proof from issue #292 not run on this pod.
