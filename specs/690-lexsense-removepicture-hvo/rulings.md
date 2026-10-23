# Issue #690 -- lex-lead ruling

**Date:** 2026-10-23  
**Issue:** #690 (P2) -- LexSenseOperations RemovePicture HVO membership  
**Parent triage:** #688 LexSense MovePicture HVO family; #471 lexicon media re-parent

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#690** filed this run (RemovePicture sibling gap left out of #688 / PR #689)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `RemovePicture`, locate the picture on the sense when any member of
   `PicturesOS` shares `picture.Hvo`, not `picture in PicturesOS`.
2. Call `PicturesOS.Remove` on the **sequence member** whose HVO matched, not
   necessarily the caller's handle reference.
3. Tag the lookup with `issue #690` in comments.
4. Do not refactor unrelated LexSenseOperations picture paths in this PR.

**Out of scope:** `MovePicture` (issue #688), Example/Pronunciation media paths.

## Verification plan

- Offline: `tests/operations/test_issue690_lexsense_removepicture_hvo_offline.py`
- Live: `tests/operations/test_issue690_lexsense_removepicture_hvo_live.py`
- Evidence: `specs/690-lexsense-removepicture-hvo/evidence/`
