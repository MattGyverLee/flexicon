# Issue #648 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #648 (P2) -- POSOperations Duplicate insert_after SubPossibilitiesOS / PossibilitiesOS index  
**Parent triage:** #597 VariantOperations; #642 Etymology; #646 Allomorph Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#648** filed this run (POSOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source POS in
   `SubPossibilitiesOS` (subcategory) or top-level `PossibilitiesOS` by comparing
   each member's `Hvo` to `source.Hvo`, not `IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #648` in comments.
4. Do not refactor unrelated POSOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue648_pos_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue648_pos_duplicate_hvo_live.py`
- Evidence: `specs/648-pos-duplicate-hvo/evidence/`
