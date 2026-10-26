# Issue #714 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #714 (P2) -- DataNotebookOperations AddParticipant / RemoveParticipant ParticipantsRC HVO membership  
**Parent triage:** #712 AddSource/RemoveSource sibling gap (ParticipantsRC explicitly out of scope there)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#714** filed this run (DataNotebook ParticipantsRC sibling gap)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `AddParticipant`, treat a person as already linked to the default role group when any member of that group's `ParticipantsRC` shares `person.Hvo`, not `person in ParticipantsRC`.
2. In `RemoveParticipant`, discover role groups by scanning each group's `ParticipantsRC` for matching `Hvo`, then call `Remove` on the reference-collection member from the loop.
3. Tag both lookups with `issue #714` in comments.
4. Do not refactor unrelated DataNotebook RC membership sites in this PR.

**Out of scope:** Duplicate `SubRecordsOS.IndexOf`, Reversal/LexReference RS membership, and other HVO-family gaps.

## Verification plan

- Offline: `tests/operations/test_issue714_datanotebook_participant_hvo_offline.py`
- Live: `tests/operations/test_issue714_datanotebook_participant_hvo_live.py`
- Evidence: `specs/714-datanotebook-participant-hvo/evidence/`
