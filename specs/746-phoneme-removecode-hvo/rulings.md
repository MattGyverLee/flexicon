# Issue #746 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #746 (P2) -- PhonemeOperations RemoveCode CodesOS HVO membership  
**Parent triage:** #706 NaturalClassOperations SegmentsRC HVO family

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#746** (filed this run; sibling gap after #706)

## RULING (binding)

1. In `RemoveCode`, scan `CodesOS` for the member whose `Hvo` matches the
   resolved code, then call `Remove` with that collection member reference.
2. Do not use Python `in` / `not in` on `CodesOS` for membership.
3. Tag the lookup with `issue #746` in comments.
4. Do not refactor unrelated PhonemeOperations paths in this PR.

**Out of scope:** PhonologicalRule `PhonRulesOS` / `FeatConstraintsOS` delete
membership; PossibilityItemOperations base `Delete` HVO.

## Verification plan

- Offline: `tests/operations/test_issue746_phoneme_removecode_hvo_offline.py`
- Live: `tests/operations/test_issue746_phoneme_removecode_hvo_live.py`
- Evidence: `specs/746-phoneme-removecode-hvo/evidence/`
