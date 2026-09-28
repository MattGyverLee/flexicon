# Issue #329 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** fix/329-datanotebook-ra-close-out from origin/main

## Status

Code fix landed on `main` via PR #387 (`dbdba16`, merge `e4b43c7`). Issue #329
remained open because the merge commit did not carry a `closes #329` keyword.
The `[Unreleased]` CHANGELOG entry for #329 is already on `main`.

## RULING (binding, close-out only)

1. Close #329 with this PR; no further LCM behaviour change.
2. Evidence remains under `specs/329-datanotebook-ra/evidence/` and the
   original ruling in `rulings.md`.
3. Offline ratchet: `tests/operations/test_issue329_datanotebook_ra.py`
   (`TestIssue329DataNotebookRaStaticLock`).

## Verification

- Offline: `python -m pytest tests/operations/test_issue329_datanotebook_ra.py -m "not requires_live_project" -q`
- Live: `specs/329-datanotebook-ra/evidence/live-status-roundtrip.md` (PR #387 /
  `TestIssue329DataNotebookStatusRoundTripLive` on `target_sandbox`).
