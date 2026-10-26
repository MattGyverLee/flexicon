# Issue #764 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #764 (P2) -- PersonOperations Delete HVO membership  
**Parent triage:** #762 lex-lead ruling out-of-scope note (Person Delete sibling gap)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#764** (filed this run; Person Delete path)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the `PeopleOA.PossibilitiesOS` member whose `Hvo`
   matches the resolved person before calling `Remove`.
2. Do not pass the caller's bare handle directly to `Remove` without an HVO scan.
3. Tag lookups with `issue #764` in comments.
4. Do not refactor unrelated PersonOperations paths in this PR.

**Out of scope:** LexReferenceOperations ref-type Delete PossibilitiesOS HVO (next sibling gap).

## Verification plan

- Offline: `tests/operations/test_issue764_person_delete_hvo_offline.py`
- Live: `tests/operations/test_issue764_person_delete_hvo_live.py`
- Evidence: `specs/764-person-delete-hvo/evidence/`
