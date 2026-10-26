# Issue #704 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #704 (P2) -- MorphRuleOperations ReorderAffixTemplates AffixTemplatesOS HVO membership  
**Parent triage:** #694 Example Reorder HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has PR #641)
- Open **P2/P3** bugs without an open PR: **#704** filed this run (ReorderAffixTemplates sibling gap)

## RULING (binding)

1. In `ReorderAffixTemplates`, validate `ordered_templates` against `pos.AffixTemplatesOS` by comparing
   `Hvo` values, not Python object identity in a `set`.
2. Build the sequence passed to `_ApplySequenceOrder` exclusively from members
   returned by iterating `AffixTemplatesOS` (matched by HVO), never from caller proxy
   objects directly.
3. Reject duplicate HVOs in `ordered_templates`.
4. Tag the partition with `issue #704` in comments.
5. Do not refactor unrelated MorphRuleOperations paths in this PR.

**Out of scope:** Other Reorder set-equality paths already tracked (#692-#700); Duplicate IndexOf family.

## Verification plan

- Offline: `tests/operations/test_issue704_morphrule_reorder_hvo_offline.py`
- Live: `tests/operations/test_issue704_morphrule_reorder_hvo_live.py`
- Evidence: `specs/704-morphrule-reorder-hvo/evidence/`
