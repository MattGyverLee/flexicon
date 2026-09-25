# Issue #521 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #521 (P2) -- SegmentOperations MergeSegments raw Owner compare; missing GetOwningParagraph  
**Parent triage:** #519 Paragraph GetOwningText; Segment Delete already uses `_GetTypedOwner`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (filed **#521** this run)

## RULING (binding)

1. Add `@OperationsMethod GetOwningParagraph(self, segment_or_hvo)` on
   `SegmentOperations`.
2. Resolve with `__GetSegmentObject`, then `para = _GetTypedOwner(segment_obj)`.
3. If `para` is None, raise
   `FP_ParameterError("Segment has no valid owning paragraph")`.
4. Return the typed paragraph (cast via `_GetTypedOwner` / `cast_to_concrete`).
5. Refactor `SetBaselineText` and `SplitSegment` to obtain the paragraph via
   `GetOwningParagraph(segment_obj)` instead of `segment_obj.Paragraph`.
6. In `MergeSegments`, replace `seg1.Owner != seg2.Owner` with typed-owner HVO
   comparison (`_GetTypedOwner(seg1).Hvo != _GetTypedOwner(seg2).Hvo`), reusing
   the survivor paragraph from the typed owner.

**Out of scope:** New segment CRUD; Paragraph/Discourse owner helpers.

## Verification plan

- Offline: `tests/operations/test_issue521_segment_get_owning_paragraph_offline.py`
- Live: `tests/operations/test_issue521_segment_get_owning_paragraph_live.py`
- Evidence: `specs/521-segment-get-owning-paragraph/evidence/`
