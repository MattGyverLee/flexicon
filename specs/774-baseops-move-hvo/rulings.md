# Issue #774 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #774 (P2) -- BaseOperations move helpers HVO index lookup  
**Parent triage:** #692 LexSense Reorder / #694 Example Reorder HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none** (#640 has PR #641)
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#774** filed this run (BaseOperations move sibling gap)

## RULING (binding)

1. `MoveUp`, `MoveDown`, and `MoveToIndex` locate the target item in the
   owning sequence by comparing each member's `Hvo` to the argument's `Hvo`,
   not `sequence[i] == item`.
2. `MoveBefore`, `MoveAfter`, and `Swap` index sequence members the same way.
3. `_FindCommonSequence` treats a sequence as containing an item when any
   member's `Hvo` matches that item's `Hvo`.
4. Tag helpers with `issue #774` in comments where the lookup is performed.
5. Do not refactor `_ApplySequenceOrder`, `Sort`, or domain-specific Reorder
   methods in this PR (separate issues #692/#694 family).

## Verification plan

- Offline: `tests/operations/test_issue774_baseops_move_hvo_offline.py`
- Live: `tests/operations/test_issue774_baseops_move_hvo_live.py`
- Evidence: `specs/774-baseops-move-hvo/evidence/`
