# Issue #492 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-25  
**HEAD:** fix/492-possibility-resolver-cast-close-out from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#492** (behaviour fix merged via PR #496;
  issue still open; no `closes #492` on merge)
- Open **P3** bugs without an open PR: **none** (#494 has open fix PR #498)
- **Selected #492** close-out this run

## Status

Behaviour fix landed on `main` via PR #496 (`bfd8c47`, merge `eb88719`).
Offline ratchet and `target_sandbox` live gates were added with that PR.
Binding fix shape is recorded in `specs/492-possibility-resolver-cast/rulings.md`.

## RULING (binding, close-out only)

1. No further LCM behaviour change -- resolvers match the original ruling
   (`cast_to_concrete` on every path; isinstance + ClassName union on HVO).
2. Close #492 with this PR.

## Verification

- Offline: `python3 -m pytest tests/operations/test_issue492_possibility_resolver_cast_offline.py -m "not requires_live_project" -q`
- Live: `tests/operations/test_issue492_possibility_resolver_cast_live.py`
  (`FLEXLIBS_REQUIRE_LIVE=1`, `target_sandbox`). **FAIL: unverified** on Cursor
  cloud (Linux, no FieldWorks / pythonnet). Gates remain for Windows live CI.
