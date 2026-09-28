# Issue #472 -- lex-lead ruling (cron)

**Date:** 2026-09-25  
**HEAD:** fix/472-possibility-reparent from origin/main

## RULING (binding)

1. **Move semantics (same as #448):** On any LCM owning sequence, never
   `Remove(ownee)` before `Add`/`Insert` to effect a move or re-parent.
   `Remove` deletes the object; re-parent with a single destination `Add`.

2. **LocationOperations.SetRegion:** Drop all `Remove(location)` calls. When
   the parent changes, `Add(location)` on the new parent's `SubPossibilitiesOS`
   or the top-level `LocationsOA.PossibilitiesOS`. No-op when
   `old_parent == new_parent`.

3. **PublicationOperations.SetIsDefault:** Source and destination are the same
   `PossibilitiesOS`. Use `MoveTo` (same index adjustment as
   `BaseOperations.MoveToIndex` / `MoveDown`) instead of `Remove` +
   `Insert`/`Add`.

4. **Scope:** This PR closes #472 only. Parallel P0s (#470, #471, #473) stay
   on their own tracks.

## Verification plan

- Offline: mock tests + AST ratchets forbidding destructive Remove in
  `SetRegion` / `SetIsDefault`.
- Live: Target sandbox -- `SetRegion` with a sub-location, `SetIsDefault` on
  a publication; re-read GUIDs after each call (`FLEXLIBS_REQUIRE_LIVE=1`).
