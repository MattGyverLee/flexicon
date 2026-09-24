# Issue #231 slice 2 -- offline evidence

## Command

```text
python3 -m pytest tests/operations/test_issue231_allomorph_remove_orphaned.py -m "not requires_live_project" -q
```

## Result

```
6 passed
```

## Live

- `run_mode`: not applicable (cloud agent; no FieldWorks)
- Live LCM: **FAIL: unverified**

Executed on 2026-09-24 in worktree `.worktrees/fix-231-slice2`.
