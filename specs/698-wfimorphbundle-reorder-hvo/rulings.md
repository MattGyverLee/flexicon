# Issue #698 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #698 (P2) -- WfiMorphBundleOperations Reorder MorphBundlesOS HVO membership  
**Parent triage:** #692 / #694 / #696 Reorder HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has PR #641)
- Open **P2/P3** bugs without an open PR: **#698** filed this run (WfiMorphBundle Reorder sibling gap noted as out-of-scope in #696 ruling)

## RULING (binding)

1. In `Reorder`, validate `bundle_list` against `analysis.MorphBundlesOS` by comparing
   `Hvo` values, not Python object identity in a `set`.
2. Build the sequence passed to `_ApplySequenceOrder` exclusively from members
   returned by iterating `MorphBundlesOS` (matched by HVO), never from caller proxy
   objects directly.
3. Resolve each list item via `__GetBundleObject` before comparing HVOs.
4. Reject duplicate HVOs in `bundle_list`.
5. Tag the partition with `issue #698` in comments.
6. Do not refactor unrelated WfiMorphBundleOperations paths in this PR.

**Out of scope:** MorphRule ReorderAffixTemplates; Duplicate IndexOf family.

## Verification plan

- Offline: `tests/operations/test_issue698_wfimorphbundle_reorder_hvo_offline.py`
- Live: `tests/operations/test_issue698_wfimorphbundle_reorder_hvo_live.py`
- Evidence: `specs/698-wfimorphbundle-reorder-hvo/evidence/`
