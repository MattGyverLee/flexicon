# Issue #700 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #700 (P2) -- PronunciationOperations Reorder PronunciationsOS HVO membership  
**Parent triage:** #694 Example Reorder HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has PR #641)
- Open **P2/P3** bugs without an open PR: **#700** filed this run (Pronunciation Reorder sibling gap)

## RULING (binding)

1. In `Reorder`, validate `pronunciation_list` against `entry.PronunciationsOS` by comparing
   `Hvo` values, not Python object identity via `_ApplySequenceOrder`'s implicit set checks on caller proxies.
2. Build the sequence passed to `_ApplySequenceOrder` exclusively from members
   returned by iterating `PronunciationsOS` (matched by HVO), never from caller proxy
   objects directly.
3. Reject duplicate HVOs in `pronunciation_list`.
4. Tag the partition with `issue #700` in comments.
5. Do not refactor unrelated PronunciationOperations paths in this PR.

**Out of scope:** BaseOperations `_ApplySequenceOrder` identity comparisons for MoveTo loop (sequence members only); MorphRule ReorderAffixTemplates; Duplicate IndexOf family.

## Verification plan

- Offline: `tests/operations/test_issue700_pronunciation_reorder_hvo_offline.py`
- Live: `tests/operations/test_issue700_pronunciation_reorder_hvo_live.py`
- Evidence: `specs/700-pronunciation-reorder-hvo/evidence/`
