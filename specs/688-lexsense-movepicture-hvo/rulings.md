# Issue #688 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #688 (P2) -- LexSenseOperations MovePicture HVO membership  
**Parent triage:** #686 Pronunciation MoveMediaFile HVO family; #471 lexicon media re-parent

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#688** filed this run (LexSense MovePicture sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `MovePicture`, treat the picture as linked to the source sense when any
   member of `PicturesOS` shares `picture.Hvo`, not `picture in PicturesOS`.
2. Keep the #471 re-parent path (`to_sense.PicturesOS.Add(picture)` only).
3. Tag the lookup with `issue #688` in comments.
4. Do not refactor unrelated LexSenseOperations picture paths in this PR.

**Out of scope:** `RemovePicture` membership check, Example/Pronunciation media paths.

## Verification plan

- Offline: `tests/operations/test_issue688_lexsense_movepicture_hvo_offline.py`
- Live: `tests/operations/test_issue688_lexsense_movepicture_hvo_live.py`
- Evidence: `specs/688-lexsense-movepicture-hvo/evidence/`
