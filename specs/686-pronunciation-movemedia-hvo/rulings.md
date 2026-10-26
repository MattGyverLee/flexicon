# Issue #686 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #686 (P2) -- PronunciationOperations MoveMediaFile HVO membership  
**Parent triage:** #684 Example MoveMediaFile sibling gap; #471 lexicon media re-parent

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#686** filed this run (Pronunciation MoveMediaFile sibling gap after #684)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `MoveMediaFile`, treat media as linked to the source pronunciation when any
   member of `MediaFilesOS` shares `media.Hvo`, not `media in MediaFilesOS`.
2. Keep the #471 re-parent path (`to_pron.MediaFilesOS.Add(media)` only).
3. Tag the lookup with `issue #686` in comments.
4. Do not refactor unrelated PronunciationOperations media paths in this PR.

**Out of scope:** LexSenseOperations MovePicture, DataNotebook RemoveMediaFile gaps.

## Verification plan

- Offline: `tests/operations/test_issue686_pronunciation_movemedia_hvo_offline.py`
- Live: `tests/operations/test_issue686_pronunciation_movemedia_hvo_live.py`
- Evidence: `specs/686-pronunciation-movemedia-hvo/evidence/`
