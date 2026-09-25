# Issue #519 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #519 (P2) -- ParagraphOperations missing GetOwningText  
**Parent triage:** #515 Discourse GetOwningText; #517 Duplicate parent chain

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (all prior issues closed)
- **Filed and selected #519** this run: no public StText→IText owner resolver on
  paragraphs; manual `.Owner` walks remain #275 Defect 1 for callers

## RULING (binding)

1. Add `@OperationsMethod GetOwningText(self, paragraph_or_hvo)` on
   `ParagraphOperations`.
2. Resolve with `__GetParagraphObject`, then `st_text = _GetTypedOwner(para_obj)`.
3. If `st_text` is None or `st_text.Owner` is None, raise
   `FP_ParameterError("Paragraph has no valid owning text")`.
4. Return `self.__GetTextObject(st_text.Owner)` (#508 ClassName cast).
5. Refactor `Duplicate` to call `GetOwningText(para_obj)` instead of inlining
   the same chain (no behaviour change).

**Out of scope:** DataNotebook text-link cast helpers; Discourse chart paths.

## Verification plan

- Offline: `tests/operations/test_issue519_paragraph_get_owning_text_offline.py`
- Live: `tests/operations/test_issue519_paragraph_get_owning_text_live.py`
- Evidence: `specs/519-paragraph-get-owning-text/evidence/`
