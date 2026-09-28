# Issue #543 -- lex-lead ruling

**Date:** 2026-09-26  
**HEAD:** fix/543-get-infl-aff-msa-slots from origin/main

## RULING (binding)

`SetInflAffMsaSlots` (#258) writes `IMoInflAffMsa.SlotsRC` but scripts still
drop to raw LCM to read slot membership for audits ("unslotted inflectional
affixes"). This is a missing read wrapper on an existing write path, not an
API-design question.

**In scope (#543):**

1. Add `MSAOperations.GetInflAffMsaSlots(sense_or_msa) -> list` as the reader
   pair for `SetInflAffMsaSlots`.
2. Accept the same shapes the setter accepts: `ILexSense` (or HVO), an
   inflectional-affix MSA object (or HVO), or a `MorphosyntaxAnalysis` wrapper
   (via existing `__Resolve` unwrapping).
3. Return slot objects in `SlotsRC` collection order -- the same LCM
   `IMoInflAffixSlot` instances callers pass into `SetInflAffMsaSlots`.
4. When the target has no MSA, a non-inflectional MSA, or an empty `SlotsRC`,
   return `[]` (read-side lenience; the setter continues to raise
   `FP_ParameterError` on wrong MSA type).
5. Read-only: no `_EnsureWriteEnabled`, no transaction bracket.

**Out of scope:** slot name / optional resolution (#542); feature-structure
readback (#544); changing `SetInflAffMsaSlots` behaviour.

## Verification plan

- Offline: source ratchet on `GetInflAffMsaSlots` (uses `SlotsRC`, no write
  guard, returns list).
- Live: `target_sandbox` -- create infl-aff MSA with slots via
  `SetInflAffMsaSlots`, re-read via `GetInflAffMsaSlots` from sense and from
  MSA HVO; confirm HVO set matches fresh `Object(hvo)` query.
