# Issue #357 -- offline verification

## Command

```
python3 -m pytest tests/operations/test_issue357_clause_marker_getwordgroup_offline.py -m "not requires_live_project" -q
```

## Result

Run on 2026-09-24 in worktree `.worktrees/fix-357-wordgroup-ra`.

## Live

**FAIL: unverified** -- cloud agent has no FieldWorks / pythonnet LCM runtime.
