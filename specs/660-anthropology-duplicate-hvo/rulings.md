# Issue #660 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #660 (P2) -- AnthropologyOperations Duplicate insert_after HVO index  
**Parent triage:** #652 LocationOperations; #597 VariantOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#660** filed this run (AnthropologyOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source anthropology item in
   `SubPossibilitiesOS` or top-level `AnthroListOA.PossibilitiesOS` by comparing each
   member's `Hvo` to `source.Hvo`, not `IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #660` in comments.
4. Do not refactor unrelated AnthropologyOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites (PossibilityListOperations, AnnotationDefOperations, possibility_item_base).

## Verification plan

- Offline: `tests/operations/test_issue660_anthropology_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue660_anthropology_duplicate_hvo_live.py`
- Evidence: `specs/660-anthropology-duplicate-hvo/evidence/`
