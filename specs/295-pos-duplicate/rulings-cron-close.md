# Issue #295 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** fix/295-pos-duplicate-close-out from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR.
- All open **P2** bugs (#230, #231, #265, #279) already have in-flight cron
  PRs (#422, #427, #426, #437).
- Selected **P3 #295** (open bug, no open PR): mock regression landed on
  `main` via PR #428; issue remained open without `closes #295`.

## Status

Behaviour coverage landed on `main` via PR #428 (`test_pos_duplicate.py`).
The `[Unreleased]` CHANGELOG bullet for #295 is already on `main`. Binding
fix shape is recorded in `specs/295-pos-duplicate/rulings.md` (test-only
slice; `Duplicate` uses correct OS `Insert`/`Add` semantics per #163).

## RULING (binding, close-out only)

1. No further code change -- offline ratchet pins OS placement for
   `POSOperations.Duplicate` (`SubPossibilitiesOS` / `PossibilitiesOS`).
2. Close #295 with this PR.

## Verification

- Offline: `python -m pytest tests/operations/test_pos_duplicate.py -m "not requires_live_project" -q`
- Live: not required (mock API-shape regression, not LCM semantics).
