# Issue #664 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #664 (P2) -- CheckOperations Duplicate insert_after PossibilitiesOS / SubPossibilitiesOS index  
**Parent triage:** #642–#662 Duplicate insert_after HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#664** filed this run (CheckOperations sibling gap on main)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source check in
   `PossibilitiesOS` (top-level list) or `SubPossibilitiesOS` (sub-check) by comparing
   each member's `Hvo` to `check_obj.Hvo`, not `IndexOf(check_obj)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #664` in comments.
4. Do not refactor unrelated CheckOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites (e.g. AnnotationDefOperations #665 follow-up).

## Verification plan

- Offline: `tests/operations/test_issue664_check_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue664_check_duplicate_hvo_live.py`
- Evidence: `specs/664-check-duplicate-hvo/evidence/`
