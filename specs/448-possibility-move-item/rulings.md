# Issue #448 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/448-possibility-move-item from origin/main

## RULING (binding)

1. **Owner classification:** Any object that is not `CmPossibilityList` but
   exposes `SubPossibilitiesOS` is a possibility parent (covers `PartOfSpeech`,
   `CmSemanticDomain`, `CmAnthroItem`, `CmCustomItem`, and the base
   `CmPossibility`). Centralise this in `__OwnerIsPossibilityItem` and use it
   in `GetParentItem` and `__GetListOwner`. Do not match only
   `ClassName == "CmPossibility"`.

2. **Move semantics:** `MoveItem` must re-parent with a single `Add` (or
   `Insert` if index support is added later) on the destination owning
   sequence. **Never** `Remove` then `Add` -- `LcmOwningSequence.Remove`
   deletes the ownee and would destroy POS subtrees and MSA references (P0).

3. **Scope:** `PossibilityListOperations` only for this PR. `POSOperations`
   already discriminates `PartOfSpeech` for `GetParent`; no change required
   there unless a shared helper is extracted later.

## Verification plan

- Offline: mock tests for `GetParentItem` / `MoveItem` with `PartOfSpeech`
  owners; AST ratchet forbids `Remove(item)` inside `MoveItem`.
- Live: on `target_sandbox`, create nested TEST_ POS items, move to top level
  and back via `MoveItem`, re-read GUID and `GetParentItem` from LCM
  (`FLEXLIBS_REQUIRE_LIVE=1`; cloud agent: **FAIL: unverified**).
