# Issue #305 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/305-complex-form-types from origin/main

## RULING (binding)

`VariantOperations.GetAllTypes()` already exposes `LexDbOA.VariantEntryTypesOA`
structurally. The complex-form analogue is `LexDbOA.ComplexEntryTypesOA` --
same `PossibilitiesOS` / `SubPossibilitiesOS` shape, localized list name, not
portable via `PossibilityLists.FindList("Complex Form Types")`.

**Correct behaviour (issue #305 scope):**

1. **`LexEntryOperations.GetAllComplexFormTypes`** -- Yield types from
   `self.project.lp.LexDbOA.ComplexEntryTypesOA.PossibilitiesOS`, including
   subtypes, with `cast_to_concrete()` (same #270 pattern as
   `VariantOperations.GetAllTypes`). Return an empty enumerable when the list
   is missing.
2. **`LexEntryOperations.FindComplexFormType(name)`** -- Case-insensitive match
   over `GetAllComplexFormTypes()` by analysis-WS name (same search shape as
   `VariantOperations.FindType`). Return `None` when not found.

**Out of scope:** A new top-level `ComplexFormOperations` class, GUID-based
built-in list lookup, returning the complex form's own `LexEntryRef`, and
`GetComplexFormTypeName` (callers can use existing possibility list helpers on
the returned type objects).

## Verification plan

- Offline: source ratchet on `LexEntryOperations`; add collection-cast pattern
  row mirroring `VariantOperations.GetAllTypes`.
- Live: read-only enumerate + `FindComplexFormType("Composto")` on Sena 3 when
  LCM available (`requires_live_project`).
