# Issue #488 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #488 (P2) -- PhonemeOperations `__GetCodeObject` uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#459 fix merged as PR #460; issue still open -- close separately)
- Open **P3** bugs without an open PR: **#459**, **#284** (re-triage tracking)
- **Filed and selected #488** this run from the #284 inventory (`__GetCodeObject` at `PhonemeOperations.py:1332`; `RemoveCode` uses `CodesOS` membership at :929)

## RULING (binding)

Cast `__GetCodeObject` through `cast_to_concrete` on every path. Match
`NaturalClassOperations.__GetPhonemeObject` (#483 family) and the #459 / #268
cast pattern. Do not return uncast objects on the HVO path.

## Verification plan

- Offline: `tests/operations/test_issue488_phoneme_code_resolver_cast_offline.py`
- Live: `target_sandbox` gate calling `RemoveCode(phoneme_hvo, code_hvo)` with
  genuine HVO ints only (`requires_live_project`).
