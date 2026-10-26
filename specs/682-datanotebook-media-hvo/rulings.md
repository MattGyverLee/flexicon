# Issue #682 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #682 (P2) -- DataNotebookOperations AddMediaFile / RemoveMediaFile HVO membership  
**Parent triage:** #680 NoteOperations Delete HVO family; #650 DataNotebook Duplicate HVO (open PR)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#682** filed this run (DataNotebook media sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `AddMediaFile`, treat a file as already linked when any member of
   `MediaFilesOS` shares `media_file.Hvo`, not `media_file in MediaFilesOS`.
2. In `RemoveMediaFile`, scan `MediaFilesOS` by `Hvo` and call `Remove` on the
   sequence member reference from the loop.
3. Tag both lookups with `issue #682` in comments.
4. Do not refactor unrelated DataNotebook RC/OS membership sites in this PR.

**Out of scope:** ResearchersRC/LocationsRC `in` checks, Duplicate `IndexOf` (#650 open PR).

## Verification plan

- Offline: `tests/operations/test_issue682_datanotebook_media_hvo_offline.py`
- Live: `tests/operations/test_issue682_datanotebook_media_hvo_live.py`
- Evidence: `specs/682-datanotebook-media-hvo/evidence/`
