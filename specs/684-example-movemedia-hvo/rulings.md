# Issue #684 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #684 (P2) -- ExampleOperations MoveMediaFile HVO membership  
**Parent triage:** #682 DataNotebook media HVO family; #471 lexicon media re-parent

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#684** filed this run (Example MoveMediaFile sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `MoveMediaFile`, treat media as linked to the source example when any
   member of `MediaFilesOS` shares `media.Hvo`, not `media in MediaFilesOS`.
2. Keep the #471 re-parent path (`to_example.MediaFilesOS.Add(media)` only).
3. Tag the lookup with `issue #684` in comments.
4. Do not refactor unrelated ExampleOperations media paths in this PR.

**Out of scope:** PronunciationOperations MoveMediaFile, RemoveMediaFile sequence
member reference gaps.

## Verification plan

- Offline: `tests/operations/test_issue684_example_movemedia_hvo_offline.py`
- Live: `tests/operations/test_issue684_example_movemedia_hvo_live.py`
- Evidence: `specs/684-example-movemedia-hvo/evidence/`
