# Issue #281 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** fix/281-lcm-casting-logger-close-out from origin/main

## Status

Behaviour fix landed on `main` via PR #397 (`2026f996`). Issue #281 remained
open because the merge commit did not carry a `closes #281` keyword. The
offline ratchet and binding ruling already live under
`specs/281-lcm-casting-logger/rulings.md`; this close-out records cron triage
and closes the issue.

## RULING (binding, close-out only)

1. No further LCM behaviour change -- module-scope `import logging`,
   `logger = logging.getLogger(__name__)`, and `logger.debug` on unregistered
   `ClassName` / failed cast paths in `cast_to_concrete` match
   `specs/281-lcm-casting-logger/rulings.md`.
2. Close #281 with this PR.

## Verification

- Offline: `python -m pytest tests/test_issue281_lcm_casting_logger.py -m "not requires_live_project" -q`
- Live: not required (no LCM write path).
