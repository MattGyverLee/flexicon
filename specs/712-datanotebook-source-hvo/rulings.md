# Issue #712 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #712 (P2) -- DataNotebookOperations AddSource/RemoveSource SourcesRC HVO  
**Parent triage:** #710 LocationsRC; #708 ResearchersRC family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#712** filed this run (SourcesRC sibling gap)

## RULING (binding)

1. In `AddSource`, treat the source as already linked when any member of
   `record.SourcesRC` has the same `Hvo` as the caller's source object; do
   not use Python `in` on the RC.
2. In `RemoveSource`, iterate `SourcesRC`, find the member whose `Hvo`
   matches, and pass that member reference to `Remove`.
3. Tag the lookup with `issue #712` in comments.
4. Do not refactor unrelated DataNotebookOperations paths in this PR.

**Out of scope:** ParticipantsRC, ResearchersRC, LocationsRC (separate issues), and other RC/OS membership sites.

## Verification plan

- Offline: `tests/operations/test_issue712_datanotebook_source_hvo_offline.py`
- Live: `tests/operations/test_issue712_datanotebook_source_hvo_live.py`
- Evidence: `specs/712-datanotebook-source-hvo/evidence/`
