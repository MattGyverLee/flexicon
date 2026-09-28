# Issue #341 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** fix/341-cm-possibility-close-out from origin/main

## Status

Code fix landed on `main` via PR #419 (`27782b0`, merge `f3a2174`). Issue #341
remained open because the merge commit did not carry a `closes #341` keyword.
The `[Unreleased]` CHANGELOG entry for #341 is already on `main`.

## RULING (binding, close-out only)

1. Close #341 with this PR; no further LCM behaviour change.
2. Evidence remains under `specs/341-cm-possibility-create/evidence/` and the
   original ruling in `rulings.md`.
3. Offline ratchet: `tests/test_issue341_possibility_create_pattern.py`
   (parameterless `factory.Create()` in possibility-creation helpers).

## Verification

- Offline: `python -m pytest tests/test_issue341_possibility_create_pattern.py -m "not requires_live_project" -q`
- Live: not required (doc/wrapper surface; no new write path beyond existing
  `CreateItem` / `CreateItemInListByName`).
