# Issue #716 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #716 (P2) -- ReversalIndexEntryOperations AddSense / RemoveSense SensesRS HVO membership  
**Parent triage:** DataNotebook/Lexicon RC HVO family (#708/#714); SensesRS on reversal entries was not covered.

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#716** filed this run (ReversalIndexEntry SensesRS sibling gap)

Untrusted open issues ignored per automation policy (non MattGyverLee / Claude / Cursor authors).

## RULING (binding)

1. In `AddSense`, treat a sense as already linked when any member of `SensesRS`
   shares `sense.Hvo`, not `sense in SensesRS`.
2. In `RemoveSense`, scan `SensesRS` by `Hvo` and call `Remove` on the
   reference-sequence member from the loop.
3. Tag both lookups with `issue #716` in comments.
4. Do not refactor unrelated RC/OS membership sites in this PR.

**Out of scope:** LexSense RC fields, Overlay PossItemsRC, and other `in` checks (separate follow-ups).

## Verification plan

- Offline: `tests/operations/test_issue716_reversal_sense_hvo_offline.py`
- Live: `tests/operations/test_issue716_reversal_sense_hvo_live.py`
- Evidence: `specs/716-reversal-sense-hvo/evidence/`
