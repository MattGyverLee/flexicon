# Issue #694 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #694 (P2) -- ExampleOperations Reorder ExamplesOS HVO membership  
**Parent triage:** #692 LexSense Reorder HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has PR #641)
- Open **P2/P3** bugs without an open PR: **#694** filed this run (Example Reorder sibling gap)

## RULING (binding)

1. In `Reorder`, validate `example_list` against `sense.ExamplesOS` by comparing
   `Hvo` values, not Python object identity in a `set`.
2. Build the sequence passed to `_ApplySequenceOrder` exclusively from members
   returned by iterating `ExamplesOS` (matched by HVO), never from caller proxy
   objects directly.
3. Reject duplicate HVOs in `example_list`.
4. Tag the partition with `issue #694` in comments.
5. Do not refactor unrelated ExampleOperations paths in this PR.

**Out of scope:** Etymology/WfiMorphBundle Reorder set-equality paths; Duplicate IndexOf family.

## Verification plan

- Offline: `tests/operations/test_issue694_example_reorder_hvo_offline.py`
- Live: `tests/operations/test_issue694_example_reorder_hvo_live.py`
- Evidence: `specs/694-example-reorder-hvo/evidence/`
