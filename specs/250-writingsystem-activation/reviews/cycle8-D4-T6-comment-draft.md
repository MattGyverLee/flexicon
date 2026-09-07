# DRAFT -- NOT POSTED

**Status:** DRAFT ONLY. Needs the user's explicit approval before anything is
posted to GitHub. Contingent on the cycle-8 #250 Defect-4 gate returning
PASS (cycle-8 archivist audit of commit `269b6a7`: PASS, no FAIL/CONCERN
rows -- see `cycle8-archivist-269b6a7-audit.md` in this same directory).
Do not run `gh` against this text without a separate, explicit go-ahead.

---

## Proposed comment body for issue #250

Defect 4 (case/separator normalization divergence between the
writing-system lookup helpers and the sync write path's
`{ws.Id: ws.Handle}` maps) is now fixed, independently of Defects 1-3.

**Defects 1-3 remain open. This issue must NOT be closed.** The fix lands
only the Defect-4 slice; the missing-Activate-API question, the
`Exists`/`Create` semantics, and the silent-vs-loud drop question are all
still unresolved and tracked here.

### Coverage boundary -- read before assuming this closes the whole symptom

The fix reaches `BaseOperations._apply_props_loop` only -- **1 of 3**
self-resolving writing-system resolution sites in the codebase. It does
**not** reach:

- `Grammar/PhonemeOperations.__ApplyBasicIPASymbol`
- `Lexicon/ExampleOperations.ApplySyncableProperties`'s `TranslationsOC` loop

Both build their own exact-case map and run their own resolution loop
rather than delegating to the now-fixed helper.

This produces a surprising, worth-stating-plainly asymmetry: syncing a
phoneme whose writing-system id differs from the target only by case or
separator will now correctly save that phoneme's `Name` and `Description`
alts -- but will **still silently drop that same phoneme's `BasicIPASymbol`
alt**, with no warning either way. One object, one sync operation, two
different outcomes depending on which property is being written.

Closing these two sites is tracked as separate follow-up work, understood
to be two differently-sized efforts: the `PhonemeOperations` site is a
one-line substitution against the new `_resolve_ws_handle` helper; the
`ExampleOperations` site is not, since its loop attaches the new
`ICmTranslation` before writing-system resolution runs, so a raising
resolver needs the loop reordered (or a proven rollback), not a swap.

### Live vs. offline verification

Of the three ways this defect fires:

- **D4-a** (caller-supplied `ws_map` value is case/separator divergent) and
  **D4-b** (no `ws_map` at all, source and target writing systems
  legitimately disagree on subtag case) are both **proven live**: the drop
  measured on unfixed code, the save measured on fixed code, each re-read
  from the LCM after re-fetching the object.
- **D4-c** (separator divergence, e.g. `en_US` vs `en-US`) is covered
  **offline only**, against the real resolution function with fabricated
  dicts. It is not verified live because the sandbox project's only two
  active writing systems (`en`, `etu`) contain neither a `-` nor a `_` to
  flip, so the trigger cannot be constructed from real project state
  without fabricating a differently-shaped project, which is out of scope
  here. D4-c is **not** described as live-verified anywhere in this comment.

### Summary

- Fixed: writing-system id resolution in `_apply_props_loop` (the shared
  sync write path).
- Not fixed, tracked separately: the same resolution gap in
  `PhonemeOperations.__ApplyBasicIPASymbol` and
  `ExampleOperations.ApplySyncableProperties`'s `TranslationsOC` loop.
- Not fixed, this issue's original scope: Defects 1-3 (activation,
  `Create` semantics, silent-drop diagnostics).

**#250 stays open.**
