# Issue #706 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #706 (P2) -- NaturalClassOperations AddPhoneme/RemovePhoneme SegmentsRC HVO membership  
**Parent triage:** #686 MoveMediaFile / #688 MovePicture HVO membership family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#706** (filed this run)

## RULING (binding)

1. In `AddPhoneme`, treat the phoneme as already present when any `SegmentsRC`
   member shares its `Hvo`; do not use Python `in` on the reference collection.
2. In `RemovePhoneme`, scan `SegmentsRC` for the member whose `Hvo` matches,
   then call `Remove` with that collection member reference.
3. Tag both sites with `issue #706` in comments.
4. Do not refactor unrelated NaturalClassOperations paths in this PR.

**Out of scope:** PhonologicalRule `FeatConstraintsOS` membership; central
`_ApplySequenceOrder` HVO (separate follow-ups).

## Verification plan

- Offline: `tests/operations/test_issue706_naturalclass_segmentsrc_hvo_offline.py`
- Live: `tests/operations/test_issue706_naturalclass_segmentsrc_hvo_live.py`
- Evidence: `specs/706-naturalclass-segmentsrc-hvo/evidence/`
