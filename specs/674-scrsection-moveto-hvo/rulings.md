# Issue #674 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #674 (P2) -- ScrSectionOperations MoveTo same-book SectionsOS index  
**Parent triage:** #473 cross-book move; #670 SplitSegment HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#674** filed this run (ScrSection MoveTo sibling gap)

## RULING (binding)

1. In `MoveTo` when `current_book == target_book`, locate the section in
   `target_book.SectionsOS` by comparing each member's `Hvo` to `section.Hvo`,
   not `IndexOf(section)`.
2. If no member matches, skip the same-book `MoveTo` call (same outward behavior
   as `IndexOf` returning -1).
3. Tag the lookup with `issue #674` in comments.
4. Fix only the same-book branch in this PR.

**Out of scope:** Cross-book Insert path (#473), other ScrSectionOperations methods.

## Verification plan

- Offline: `tests/operations/test_issue674_scrsection_moveto_hvo_offline.py`
- Live: `tests/operations/test_issue674_scrsection_moveto_hvo_live.py`
- Evidence: `specs/674-scrsection-moveto-hvo/evidence/`
