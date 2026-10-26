# Issue #742 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #742 (P2) -- LexReferenceOperations RemoveTarget TargetsRS HVO membership  
**Parent triage:** RC/RS HVO family (#716 Reversal SensesRS, #738 ComponentLexemesRS); TargetsRS was not covered.

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#742** filed this run (LexReference TargetsRS sibling gap)

Untrusted open issues ignored per automation policy (non MattGyverLee / Claude / Cursor authors).

## RULING (binding)

1. In `RemoveTarget`, scan `TargetsRS` for a member whose `Hvo` matches the
   resolved target; call `Remove(linked)` on that member.
2. If no member shares the HVO, remain a no-op (D5 — membership test outside
   transaction unchanged in spirit).
3. Tag the lookup with `issue #742` in comments.
4. Do not refactor unrelated RC/OS membership sites in this PR.

**Out of scope:** `AddTarget` (duplicates allowed by design), MSA exception-feature RC mutators, and other `in` checks (separate follow-ups).

## Verification plan

- Offline: `tests/operations/test_issue742_lexreference_target_hvo_offline.py`
- Live: `tests/operations/test_issue742_lexreference_target_hvo_live.py`
- Evidence: `specs/742-lexreference-target-hvo/evidence/`
