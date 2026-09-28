# Issue #550 -- lex-lead ruling

**Date:** 2026-09-26  
**Issue:** #550 (P2) -- LexSenseOperations Duplicate insert_after SensesOS index  
**Parent triage:** #548 Environment Duplicate (PR #549); #540 PhonologicalRule Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#550** (filed this run; sibling IndexOf gap in Lexicon Duplicate)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source sense in
   `parent.SensesOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `SensesOS.IndexOf(source)`.
2. If no member matches, keep the existing fallback: insert at
   `len(sense_list)` (append).
3. Tag the lookup with `issue #550` in comments.
4. Do not refactor unrelated LexSenseOperations paths in this PR.

**Out of scope:** Example, Etymology, Pronunciation, and other Lexicon Duplicate
`IndexOf(source)` sites.

## Verification plan

- Offline: `tests/operations/test_issue550_lexsense_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue550_lexsense_duplicate_hvo_live.py`
- Evidence: `specs/550-lexsense-duplicate-hvo/evidence/`
