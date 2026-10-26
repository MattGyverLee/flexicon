# Issue #692 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #692 (P2) -- LexSenseOperations Reorder SensesOS HVO membership  
**Parent triage:** #550 LexSense Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has PR #641)
- Open **P2/P3** bugs without an open PR: **#692** filed this run (Reorder sibling gap)

## RULING (binding)

1. In `Reorder`, treat `sense_list` membership against `entry.SensesOS` by comparing
   `Hvo` values, not Python object identity in a `set`.
2. Build `desired_order` exclusively from the sequence members returned by iterating
   `entry.SensesOS` (matched by HVO), never from caller proxy objects directly.
3. Reject duplicate HVOs in `sense_list` and HVOs that are not on the entry.
4. Tag the partition with `issue #692` in comments.
5. Do not refactor unrelated LexSenseOperations paths in this PR.

**Out of scope:** Example/Pronunciation/Etymology Reorder set-equality paths; RC collections.

## Verification plan

- Offline: `tests/operations/test_issue692_lexsense_reorder_hvo_offline.py`
- Live: `tests/operations/test_issue692_lexsense_reorder_hvo_live.py`
- Evidence: `specs/692-lexsense-reorder-hvo/evidence/`
