# Issue #258 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/258-set-infl-aff-msa-slots from origin/main

## RULING (binding)

Users editing inflectional-affix slot membership today drop to raw LCM
(``IMoInflAffMsa(msa).SlotsRC.Remove/Add``). That is a missing wrapper on a
real write path, not an API-design question.

**In scope (#258):**

1. Add ``MSAOperations.SetInflAffMsaSlots(sense, slots, replace=True)`` mirroring
   ``SetStemMsaPos`` / ``SetDerivAffMsaPos`` conventions: write guard, param
   validation, resolve parameters before the transaction bracket (D5), and
   ``FP_ParameterError`` when the sense has no MSA or the MSA is not
   ``IMoInflAffMsa``.
2. ``replace=True`` (default): ``SlotsRC.Clear()`` then add each resolved slot.
   ``replace=False``: append only.
3. ``slots`` must be a sequence (empty allowed when clearing with
   ``replace=True``).

**Out of scope:** slot *creation* or template ordering (#255); changing MSA
family; sync payload shape for ``SlotsRC``.

## Verification plan

- Offline: source ratchet on ``SetInflAffMsaSlots`` (``SlotsRC.Clear`` when
  ``replace``, resolve-before-bracket).
- Live: ``target_sandbox`` -- create infl-aff MSA with one slot, replace with
  another, re-read ``SlotsRC`` HVOs from a fresh ``Object(hvo)`` query.
