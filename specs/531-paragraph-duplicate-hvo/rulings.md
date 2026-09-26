# Issue #531 -- lex-lead ruling

**Date:** 2026-09-26  
**Issue:** #531 (P2) -- ParagraphOperations Duplicate insert_after ParagraphsOS index  
**Parent triage:** #517 Duplicate parent chain; #523 Exists HVO membership family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (filed **#531** this run)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source paragraph in
   `owner.ParagraphsOS` by comparing each member's `Hvo` to `para_obj.Hvo`, not
   `list(...).index(para_obj)`.
2. If no member matches, keep the existing fallback: insert at
   `len(para_list)` (append).
3. Tag the lookup with `issue #531` in comments.
4. Do not refactor unrelated ParagraphOperations paths in this PR.

**Out of scope:** Other `in list(collection)` sites; SegmentOperations #528 PR.

## Verification plan

- Offline: `tests/operations/test_issue531_paragraph_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue531_paragraph_duplicate_hvo_live.py`
- Evidence: `specs/531-paragraph-duplicate-hvo/evidence/`
