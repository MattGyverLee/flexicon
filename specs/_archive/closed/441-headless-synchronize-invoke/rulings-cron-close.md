# Issue #441 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** `fix/441-close-out` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (labeled)
- Open **P2** bugs without an open PR: **none** (#231 has open PR #439)
- Selected **#441** (bug label, **P1-caliber**, no open PR): behaviour fix
  landed on `main` via PR #442; issue remained open without `closes #441`

## Status

`HeadlessLcmUI` now constructs `SingleThreadedSynchronizeInvoke` and returns it
from `SynchronizeInvoke` / `get_SynchronizeInvoke` (`headless_ui.py`). Unit
coverage is in `tests/test_headless_lcm_ui.py` (issue #441 assertions). The
`[Unreleased]` CHANGELOG bullet is on `main`. Binding fix shape is recorded in
`specs/441-headless-synchronize-invoke/rulings.md`.

## RULING (binding, close-out only)

1. No further LCM behaviour change -- inline invoker matches the issue's
   suggested fix and preserves the #238 headless deadlock avoidance
   (`InvokeRequired is False`).
2. Apply **P1** label to #441 (high: any write after HermitCrab parser load
   was broken on the default UI).
3. Close #441 with this PR.

**Out of scope (remain tracked elsewhere if needed):**
`HeadlessThreadedProgress.SynchronizeInvoke` (still null in compiled C#);
end-to-end `ParseWord` then write live repro (requires FieldWorks + HC project).

## Verification

- Offline: `python -m pytest tests/test_headless_lcm_ui.py -q`
- Live: **FAIL: unverified** on cloud agent (no FieldWorks / pythonnet runtime).
  Optional follow-up: Target/Sena sandbox with HC parser + trivial write.
