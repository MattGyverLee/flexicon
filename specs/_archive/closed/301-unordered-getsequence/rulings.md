# Issue #301 -- lex-lead ruling

**Date:** 2026-09-23  
**Issue:** #301 (P1) -- reorder APIs on unordered owning collections

## RULING

**Option 1 (binding):** Both sites override `_GetSequence` to raise
`NotImplementedError` with an explicit message that the underlying LCM
collection is an **unordered** `ILcmOwningCollection` (`...OC`), so inherited
`Sort` / `MoveUp` / `MoveDown` / `MoveToIndex` are not supported. Do **not**
rename `AnalysesOS` / `PhonemesOS` to the real `...OC` property names -- that
would only move the failure deeper into `BaseOperations` (issue body option 3,
rejected).

Apply the same message shape at both chokepoints:

- `WfiAnalysisOperations` -- parent is `IWfiWordform`; collection is
  `AnalysesOC`.
- `PhonemeOperations` -- parent is `IPhPhonemeSet`; collection is
  `PhonemesOC`.

Precedent: `ConstChartMarkerOperations._GetSequence` (issue #52) -- raise at
the sequence hook so all four inherited reorderers fail honestly.

## Pattern audit

Two independent `_GetSequence` overrides, same defect class (nonexistent `...OS`
name on an unordered `...OC`). No other Operations classes in the #277 sweep
table rows 1 and 6 remain unfixed on main. No sibling sweep beyond these two
files.

## Out of scope

- Adding a `parent` parameter to `PhonemeOperations.Create` / `GetAll` for
  reorder ergonomics (#301 "extra wrinkle") -- follow-up issue if needed.
- Removing inherited reorder methods from the public surface (option 2) -- the
  raise-at-`_GetSequence` approach matches house style and existing #52 guard.

## Verification plan

- Offline: mock regression tests calling `_GetSequence` and one inherited
  `MoveUp` per class (expect `NotImplementedError`, message mentions
  unordered / `OC`).
- Live: reflection smoke on `target_sandbox` confirming property names and
  `ILcmOwningCollection` (extend when FieldWorks is available).
