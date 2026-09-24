# Issue #359 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** fix/359-anthropology-gsp-close-out from origin/main

## Status

Code fix landed on `main` via PR #381 (`fd1ffb9`, merge `c8188b0`). Issue #359
remained open because the merge commit did not carry a `closes #359` keyword.
The `[Unreleased]` CHANGELOG entry for #359 is already on `main`.

## RULING (binding, close-out only)

1. Close #359 with this PR; no further LCM behaviour change.
2. Evidence remains under `specs/359-anthropology-gsp/evidence/` and the
   original ruling in `rulings.md`.

## Verification

- Offline: `python -m pytest tests/operations/test_anthropology_get_syncable_properties.py tests/operations/test_issue359_anthropology_gsp_offline.py -m "not requires_live_project" -q`
- Live: `specs/359-anthropology-gsp/evidence/live-359.md` (PR #381 / import regression gate).
