# Issue #483 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #483 (P2) -- NaturalClassOperations `__GetPhonemeObject` uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (#459 fix merged but issue still open; #284 is re-triage tracking; #468 is enhancement)
- **Filed and selected #483** this run from the #284 inventory (`__GetPhonemeObject` at `NaturalClassOperations.py:125`; callers use `SegmentsRC` at AddPhoneme/RemovePhoneme)

## RULING (binding)

Cast `__GetPhonemeObject` through `cast_to_concrete` on every path. Match
`__GetNaturalClassObject` in the same module and the #457 / #465 / #481
family. Do not return uncast objects on the HVO path.

## Verification plan

- Offline: source ratchet + live gate module existence.
- Live: `target_sandbox` gate calling `AddPhoneme(nc_hvo, phoneme_hvo)` with
  genuine HVO ints only (`requires_live_project`).
