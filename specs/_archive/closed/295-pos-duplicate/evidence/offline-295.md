# Issue #295 -- offline verification

## Command

```
python3 -m pytest tests/operations/test_pos_duplicate.py -m "not requires_live_project" -q
```

## Result

**PASS:** 5 passed in 0.05s (2026-09-24, cloud cron worktree).

Live LCM: not applicable (mock-only OS/OC shape regression per lex-lead ruling).
