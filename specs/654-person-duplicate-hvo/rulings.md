# Issue #654 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #654 (P2) -- PersonOperations Duplicate insert_after PeopleOA.PossibilitiesOS index  
**Parent triage:** #652 LocationOperations; #648 POSOperations Duplicate HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#654** filed this run (PersonOperations sibling gap)

## RULING (binding)

1. In `Duplicate` when `insert_after=True`, locate the source person in
   `PeopleOA.PossibilitiesOS` by comparing each member's `Hvo` to `source.Hvo`, not
   `PossibilitiesOS.IndexOf(source)`.
2. If no member matches, append at `len(sequence)` (do not insert at index 0 when lookup fails).
3. Tag the lookup with `issue #654` in comments.
4. Do not refactor unrelated PersonOperations paths in this PR.

**Out of scope:** Other Duplicate `IndexOf` sites across Operations classes.

## Verification plan

- Offline: `tests/operations/test_issue654_person_duplicate_hvo_offline.py`
- Live: `tests/operations/test_issue654_person_duplicate_hvo_live.py`
- Evidence: `specs/654-person-duplicate-hvo/evidence/`

