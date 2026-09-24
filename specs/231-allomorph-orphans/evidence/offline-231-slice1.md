# Issue #231 slice 1 -- offline evidence

## Command

```
python -m pytest tests/operations/test_issue231_allomorph_remove_orphaned.py -m "not requires_live_project" -q
```

## run_mode

Cloud agent: no `tests/live_status.json` update (mock-only tests).

## Result

Executed on 2026-09-24 in worktree `fix/231-allomorph-orphan-dupes`.

## Live LCM

**FAIL: unverified** (no FieldWorks on Linux cloud pod).
