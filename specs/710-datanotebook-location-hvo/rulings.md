# Issue #710 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #710 (P2) -- DataNotebookOperations AddLocation/RemoveLocation LocationsRC HVO  
**Parent triage:** #708 AddResearcher/RemoveResearcher; #682 AddMediaFile family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#710** filed this run (LocationsRC sibling gap)

## RULING (binding)

1. In `AddLocation`, treat the location as already linked when any member of
   `record.LocationsRC` has the same `Hvo` as the caller's location object; do
   not use Python `in` on the RC.
2. In `RemoveLocation`, iterate `LocationsRC`, find the member whose `Hvo`
   matches, and pass that member reference to `Remove`.
3. Tag the lookup with `issue #710` in comments.
4. Do not refactor unrelated DataNotebookOperations paths in this PR.

**Out of scope:** SourcesRC, ParticipantsRC, and other RC/OS membership sites.

## Verification plan

- Offline: `tests/operations/test_issue710_datanotebook_location_hvo_offline.py`
- Live: `tests/operations/test_issue710_datanotebook_location_hvo_live.py`
- Evidence: `specs/710-datanotebook-location-hvo/evidence/`
