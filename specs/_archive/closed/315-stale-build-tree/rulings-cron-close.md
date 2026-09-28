# Issue #315 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** `fix/315-stale-build-tree` from `origin/main`

## Status

Hygiene fix was already satisfied on `main`: `build/` has been listed in
`.gitignore` since the initial commit and no `build/` paths are tracked
(`git ls-files build/` is empty). Issue #315 remained open pending a formal
close-out and ratchet.

## RULING (binding, close-out)

1. Add offline ratchet `tests/test_issue315_build_hygiene.py` per
   `specs/315-stale-build-tree/rulings.md`.
2. Close #315 with this PR; no LCM or runtime behaviour change.

## Verification

- Offline: `python -m pytest tests/test_issue315_build_hygiene.py -m "not requires_live_project" -q`
- Evidence: `specs/315-stale-build-tree/evidence/offline-315.md`
