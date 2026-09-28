# Issue #471 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #471 (P0) -- Remove-then-Add in Lexicon media/picture move ops  
**Parent sweep:** #448 move-item subclass owners (section B/C)

## Triage (cron)

- Open **P0** bugs without an open PR: **#470**, **#471**, **#472**, **#473**
- Open **P1** bugs without an open PR: **none**
- Selected **#471** (smallest scoped fix mirroring landed #448 semantics)

## RULING (binding)

1. **Move semantics:** `MoveMediaFile` (Example and Pronunciation) and
   `MovePicture` must re-parent with a single `Add` on the destination owning
   sequence. **Never** `Remove` then `Add` -- `LcmOwningSequence.Remove`
   deletes the ownee (P0 data loss).

2. **Validation unchanged:** Keep membership checks on the source collection
   before the transaction; only the write path drops `Remove`.

3. **Docstrings:** Align Notes with #448 / `PossibilityListOperations.MoveItem`
   (LCM re-parents on Add; GUID preserved).

## Verification plan

- Offline: AST ratchet forbids `.Remove(media)` / `.Remove(picture)` inside the
  three move method bodies; mock sequence test that Add-only preserves object
  identity.
- Live: `target_sandbox` gate -- move media/picture, re-read GUID from LCM
  (`FLEXLIBS_REQUIRE_LIVE=1`; cloud agent: expect **FAIL: unverified** if no FLEx).
