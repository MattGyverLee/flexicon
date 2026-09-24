# Issue #315 -- offline evidence

**Date:** 2026-09-24  
**Branch:** `fix/315-stale-build-tree`

## Command

```
python3 -m pytest tests/test_issue315_build_hygiene.py -m "not requires_live_project" -q
```

## Pre-state (repo)

- `.gitignore` contains `build/` (line 13 at HEAD).
- `git ls-files build/` → empty (no tracked packaging tree).

## Post-state (ratchet)

Same constraints enforced by three offline tests (gitignore line, empty
`ls-files`, `git check-ignore` on a representative `build/lib/flexicon/` path).

## Result

**PASS:** 3 passed (2026-09-24, cloud cron worktree
`.worktrees/fix-315-stale-build-tree`). Live LCM: N/A.
