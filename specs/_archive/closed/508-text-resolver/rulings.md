# Issue #508 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #508 (P2) -- Paragraph/Discourse `__GetTextObject` #275 gap  
**Parent triage:** #275 resolver family; `TextOperations` already aligned

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (all prior P2 issues closed with merged PRs)
- Open **P3** bugs without an open PR: **none**
- **Filed and selected #508** this run: sibling `__GetTextObject` helpers in
  `ParagraphOperations` and `DiscourseOperations` still omit the ClassName cast
  path that `TextOperations` shipped under #275

## RULING (binding)

Copy the `TextOperations.__GetTextObject` resolution shape into both modules:

- HVO (`int`) path: `ClassName == "Text"` then `IText(obj)`, union with
  `isinstance(obj, IText)`, else `FP_ParameterError`.
- Pass-through path: same ClassName dispatch before returning unchanged.

Do not alter `__GetParagraphObject` in this slice (already casts `IStTxtPara`).

## Verification plan

- Offline: `tests/operations/test_issue508_text_resolver_offline.py`
- Live: `tests/operations/test_issue508_text_resolver_live.py`
  (`target_sandbox`; genuine text HVO and raw `project.Object(hvo)` pass-through)
