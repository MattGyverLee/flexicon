# Issue #666 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #666 (P2) -- AnnotationDefOperations Duplicate insert_after PossibilitiesOS / SubPossibilitiesOS index  
**Parent triage:** #642–#664 Duplicate insert_after HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#666** filed this run (AnnotationDefOperations sibling gap on main)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source definition in
   `PossibilitiesOS` (top-level list) or `SubPossibilitiesOS` (sub-definition) by comparing
   each member's `Hvo` to `source.Hvo`, not `IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #666` in comments.
4. Do not refactor unrelated AnnotationDefOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites already covered by open PRs (#642–#664).

## Verification plan

- Offline: `tests/operations/test_issue666_annotationdef_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue666_annotationdef_duplicate_hvo_live.py`
- Evidence: `specs/666-annotationdef-duplicate-hvo/evidence/`
