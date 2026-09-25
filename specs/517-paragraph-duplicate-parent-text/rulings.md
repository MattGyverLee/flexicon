# Issue #517 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #517 (P2) -- ParagraphOperations Duplicate StText→IText owner chain  
**Parent triage:** #515 GetOwningText; #508 text __GetTextObject

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#513/#515 have open PRs)
- **Filed and selected #517** this run: `Duplicate` uses `IText(owner.Owner)` after
  `_GetTypedOwner(para_obj)`; the second hop remains an uncast ICmObject view.

## RULING (binding)

1. After `_GetTypedOwner(para_obj)`, if `owner.Owner` is None raise
   `FP_ParameterError("Cannot determine parent text for paragraph")`.
2. Set `parent_text = self.__GetTextObject(owner.Owner)` — do not call bare
   `IText(owner.Owner)`.
3. Leave StText `_GetTypedOwner` on the paragraph unchanged (already correct).

**Out of scope:** Other ParagraphOperations methods; Discourse owner-cast PRs #514/#516.

## Verification plan

- Offline: `tests/operations/test_issue517_paragraph_duplicate_parent_offline.py`
- Live: `tests/operations/test_issue517_paragraph_duplicate_parent_live.py`
- Evidence: `specs/517-paragraph-duplicate-parent-text/evidence/`
