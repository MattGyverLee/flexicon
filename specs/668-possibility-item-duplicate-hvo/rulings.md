# Issue #668 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #668 (P2) -- PossibilityItemOperations Duplicate insert_after PossibilitiesOS index  
**Parent triage:** #648 POSOperations; #662 PossibilityListOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#668** filed this run (shared PossibilityItemOperations base gap)

## RULING (binding)

1. In `PossibilityItemOperations.Duplicate` when `insert_after=True`, locate the source item in
   `PossibilitiesOS` by comparing each member's `Hvo` to `source.Hvo`, not `IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #668` in comments.
4. Fix only the base class in this PR; consumers (Publications, Confidence, TranslationType) inherit the fix.

**Out of scope:** Other Duplicate `IndexOf` sites already covered by open PRs (#642-#667 family on branches).

## Verification plan

- Offline: `tests/operations/test_issue668_possibility_item_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue668_possibility_item_duplicate_hvo_live.py`
- Evidence: `specs/668-possibility-item-duplicate-hvo/evidence/`
