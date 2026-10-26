# Issue #696 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #696 (P2) -- EtymologyOperations Reorder EtymologyOS HVO membership  
**Parent triage:** #692 / #694 LexSense and Example Reorder HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has PR #641)
- Open **P2/P3** bugs without an open PR: **#696** filed this run (Etymology Reorder sibling gap noted as out-of-scope in #692/#694 rulings)

## RULING (binding)

1. In `Reorder`, validate `etymology_list` against `entry.EtymologyOS` by comparing
   `Hvo` values, not Python object identity in a `set`.
2. Build the sequence passed to `_ApplySequenceOrder` exclusively from members
   returned by iterating `EtymologyOS` (matched by HVO), never from caller proxy
   objects directly.
3. Reject duplicate HVOs in `etymology_list`.
4. Tag the partition with `issue #696` in comments.
5. Do not refactor unrelated EtymologyOperations paths in this PR.

**Out of scope:** WfiMorphBundle Reorder set-equality path; Duplicate IndexOf family.

## Verification plan

- Offline: `tests/operations/test_issue696_etymology_reorder_hvo_offline.py`
- Live: `tests/operations/test_issue696_etymology_reorder_hvo_live.py`
- Evidence: `specs/696-etymology-reorder-hvo/evidence/`
