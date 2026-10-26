# Issue #708 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #708 (P2) -- DataNotebookOperations AddResearcher / RemoveResearcher ResearchersRC HVO membership  
**Parent triage:** #682 AddMediaFile/RemoveMediaFile sibling gap (ResearchersRC explicitly out of scope there)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#708** filed this run (DataNotebook ResearchersRC sibling gap)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `AddResearcher`, treat a person as already linked when any member of
   `ResearchersRC` shares `person.Hvo`, not `person in ResearchersRC`.
2. In `RemoveResearcher`, scan `ResearchersRC` by `Hvo` and call `Remove` on the
   reference-collection member from the loop.
3. Tag both lookups with `issue #708` in comments.
4. Do not refactor unrelated DataNotebook RC membership sites in this PR.

**Out of scope:** ParticipantsRC/LocationsRC/SourcesRC `in` checks (separate follow-ups).

## Verification plan

- Offline: `tests/operations/test_issue708_datanotebook_researcher_hvo_offline.py`
- Live: `tests/operations/test_issue708_datanotebook_researcher_hvo_live.py`
- Evidence: `specs/708-datanotebook-researcher-hvo/evidence/`
