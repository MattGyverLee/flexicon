# Issue #358 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/358-show-complex-forms-in-rs from origin/main

## RULING (binding)

`ILexEntryRef` exposes **`ShowComplexFormsInRS`** (reference sequence), not
`ShowComplexFormsIn`. The existing `hasattr(item, "ShowComplexFormsIn")` guards
in `VariantOperations.GetSyncableProperties` and `Duplicate` are always false;
sync never carries the data and duplicate never copies it.

**Correct behaviour:**

1. **GetSyncableProperties** -- emit `show_complex_forms_in_rs` as an ordered
   list of target GUID strings from `item.ShowComplexFormsInRS`, matching the
   `targets_rs` pattern on `LexReferenceOperations`.
2. **Duplicate** -- copy each element of `source.ShowComplexFormsInRS` onto
   `duplicate.ShowComplexFormsInRS` in the RS copy block (same as
   `ComponentLexemesRS`).
3. Remove the phantom `ShowComplexFormsIn` paths and drop the ratchet allowlist
   entry for #358.

**Out of scope:** `ApplySyncableProperties` for variants (not implemented today);
ConfidenceOperations #363; OverlayOperations #364.

## Verification plan

- Offline: member ratchet + new unit test + targeted pytest file.
- Live: `tests/operations/test_variants_live.py` duplicate path when
  `FLEXLIBS_REQUIRE_LIVE=1` and FieldWorks are available (blocked on Linux
  cloud agent -- see evidence).
