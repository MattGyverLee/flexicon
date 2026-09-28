# Issue #295 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/295-pos-duplicate from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR.
- All seven open **P2** issues (#210, #230, #231, #258, #265, #279, #341)
  already have open cron PRs (#421-#427).
- Selected **P3 #295** (open bug, no PR): mock regression for the last
  #163-shaped OS call site.

## RULING (binding)

`POSOperations.Duplicate` uses `SubPossibilitiesOS` / `PossibilitiesOS`
(**OS**, ordered sequences). `IndexOf` + `Insert` for `insert_after=True`
and `Add` for `insert_after=False` are **correct** here -- unlike OC
siblings where Insert is invalid (#163).

**Fix for this PR (test-only):**

1. Add `tests/operations/test_pos_duplicate.py` mirroring the discourse/note
   mock pattern: assert Insert index for subcategory and top-level OS paths,
   assert Add for append, assert deep recursion adds nested subcategories via
   `SubPossibilitiesOS.Add`.
2. Module docstring must state OS-not-OC rationale (#163) so a future OC
   "fix" sweep does not silently degrade `insert_after`.
3. Do **not** change `POSOperations.Duplicate` behaviour in this slice.

**Out of scope:** Live LCM duplicate smoke (optional follow-up); changing
Duplicate implementation.

## Verification plan

- Offline: `python -m pytest tests/operations/test_pos_duplicate.py -m "not requires_live_project" -q`
- Live: not required (pins API shape, not LCM semantics).
