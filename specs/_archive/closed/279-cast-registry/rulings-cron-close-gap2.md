# Issue #279 -- lex-lead close-out ruling (cron, gap 2)

**Date:** 2026-09-24  
**HEAD:** fix/279-possibility-helpers-close-out from origin/main

## Status

- **Gap 1** (four cast-registry ClassNames) landed on `main` via PR #421.
- **Gap 2** (`FLExProject.ListFieldPossibilities` / `ListFieldLookup`) remained
  open pending an API decision (#279 body item 2).

## RULING (binding)

1. **No return-type change.** `ListFieldPossibilities` must keep returning the
   live `PossibilitiesOS` owning sequence from the list owner. Callers assign
   back into indexed slots (e.g. `sense.StatusRA = status_poss[3]`); materialising
   a Python list of cast concrete types would break load-bearing write paths and
   change the documented contract.
2. **No cast wrapper on lookup.** `ListFieldLookup` must keep returning whatever
   `FindPossibilityByName` returns (`ICmPossibility` / base interface). Casting
   inside the helper would change the helper's contract without a semver-major
   release.
3. **Document the escape hatch.** Docstrings must state that elements are
   interface-typed LCM objects and that callers who need concrete types should
   use the public `cast_to_concrete` (#271) on individual items -- not expect
   these helpers to return pre-cast lists.
4. **Close #279** with this PR once offline ratchets pass. No LCM write-path
   change; live verification is N/A.

## Verification

- Offline: `python -m pytest tests/test_issue279_possibility_helpers_ratchet.py tests/operations/test_issue279_cast_registry_offline.py -m "not requires_live_project" -q`
- Live: **N/A** (docstring / policy only).
