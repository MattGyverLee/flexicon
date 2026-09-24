# Issue #258 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** fix/258-set-infl-aff-msa-slots-close-out from origin/main

## Status

Behaviour fix landed on `main` via PR #388 (`4387e77`, merged 2026-09-23).
Issue #258 remained open because the merge commit did not carry a
`closes #258` keyword. The `[Unreleased]` CHANGELOG entry, offline ratchets,
live test scaffold, and binding implementation ruling were all delivered in
that PR; this close-out adds the formal lex-lead close-out record and closes
the issue.

## RULING (binding, close-out only)

1. No further LCM behaviour change -- `MSAOperations.SetInflAffMsaSlots`
   matches `specs/258-set-infl-aff-msa-slots/rulings.md`.
2. Close #258 with this PR.

## Verification

- Offline: `python -m pytest tests/operations/test_issue258_set_infl_aff_msa_slots_offline.py -m "not requires_live_project" -q`
- Live: unchanged from PR #388 plan (`specs/258-set-infl-aff-msa-slots/evidence/live-258.md`; **FAIL: unverified** on cloud agent).
