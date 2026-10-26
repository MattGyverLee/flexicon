# Issue #776 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #776 (P2) -- BaseOperations Sort / _ApplySequenceOrder HVO  
**Parent triage:** #774 BaseOperations move helpers (PR #775)

## Triage (cron)

- Open **P0** bugs without an open PR: **none** (#640 has PR #641)
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#776** filed this run (Sort /
  `_ApplySequenceOrder` sibling gap called out of scope in #774 ruling)

## RULING (binding)

1. `Sort` locates the item to move at each target index by comparing sequence
   members to the sorted snapshot with `_SameLcmObjectByHvo`, not `==`.
2. `_ApplySequenceOrder` validates membership with `_HvoSetForObjects` (HVO
   sets), not `set(current) != set(desired_order)`.
3. `_ApplySequenceOrder` locates `target_item` in the sequence with
   `_SameLcmObjectByHvo`, not `==`.
4. Tag lookup sites with `issue #776` in comments.
5. Reuse `_SameLcmObjectByHvo` / `_LcmObjectHvo` from #774; do not re-touch
   move helpers in this PR.

## Verification plan

- Offline: `tests/operations/test_issue776_baseops_sort_hvo_offline.py`
- Live: `tests/operations/test_issue776_baseops_sort_hvo_live.py`
- Evidence: `specs/776-baseops-sort-hvo/evidence/`
