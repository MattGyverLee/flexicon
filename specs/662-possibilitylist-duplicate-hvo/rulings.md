# Issue #662 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #662 (P2) -- PossibilityListOperations Duplicate insert_after HVO index  
**Parent triage:** #660 AnthropologyOperations; #597 VariantOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#662** filed this run (PossibilityListOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source in
   `SubPossibilitiesOS` or top-level `PossibilitiesOS` by comparing each
   member's `Hvo` to `source.Hvo`, not `IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0
   when lookup fails).
3. Tag the lookup with `issue #662` in comments.
4. Do not refactor unrelated PossibilityListOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites (e.g. AnnotationDefOperations,
`possibility_item_base`).

## Verification plan

- Offline: `tests/operations/test_issue662_possibilitylist_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue662_possibilitylist_duplicate_hvo_live.py`
- Evidence: `specs/662-possibilitylist-duplicate-hvo/evidence/`
