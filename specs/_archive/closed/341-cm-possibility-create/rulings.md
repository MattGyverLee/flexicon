# Issue #341 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/341-cm-possibility-create from origin/main

## RULING (binding)

Runtime logs showed `OverloadResolutionError` when callers invoked raw
`CmPossibilityFactory.Create(System.Guid, ICmPossibilityList)`. That overload
does not exist in LCM; the supported pattern is **parameterless**
`factory.Create()`, then attach the new `ICmPossibility` to
`PossibilitiesOS` or `SubPossibilitiesOS` before setting properties.

flexicon already implements this in `PossibilityListOperations.CreateItem`
and `PossibilityItemOperations.Create` (specialized lists such as
`Publications`, `Confidence`, etc.). Issue #341 is **discoverability**, not a
missing factory call.

**Fix for this PR:**

1. Document the anti-pattern and the flexicon entry points in
   `PossibilityListOperations` (class docstring + `CreateItem` notes).
2. Add **`CreateItemInListByName(list_name, item_name, ...)`** so callers who
   know the list label (e.g. `"Publication Types"`) never need raw LCM factory
   reflection.
3. Offline AST ratchet: possibility-creation helpers must call
   `factory.Create()` with no arguments (guards against reintroducing wrong
   overload guesses).

**Out of scope:** #279 Tier-3 `FLExProject` possibility helper return-type
decision; regenerating `expected_contract.json`; new specialized Operations
classes beyond existing `PossibilityItemOperations` subclasses.

## Verification plan

- Offline: `tests/test_issue341_possibility_create_pattern.py` (AST ratchet);
  unit test for `CreateItemInListByName` list-not-found error (mock project).
- Live: optional smoke via `PossibilityLists.CreateItem` on Target when LCM
  available; not required for doc/wrapper-only surface.
