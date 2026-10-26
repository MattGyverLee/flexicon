# Issue #652 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #652 (P2) -- LocationOperations Duplicate insert_after SubPossibilitiesOS / PossibilitiesOS index  
**Parent triage:** #597 VariantOperations; #648 POSOperations; #650 DataNotebook Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#652** filed this run (LocationOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source location in
   `SubPossibilitiesOS` (sublocation) or top-level `LocationsOA.PossibilitiesOS` by comparing
   each member's `Hvo` to `source.Hvo`, not `IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #652` in comments.
4. Do not refactor unrelated LocationOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue652_location_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue652_location_duplicate_hvo_live.py`
- Evidence: `specs/652-location-duplicate-hvo/evidence/`

