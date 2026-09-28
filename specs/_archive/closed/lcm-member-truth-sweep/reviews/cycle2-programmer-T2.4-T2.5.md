# Cycle 2 -- Programmer report: T2.4 (test rewrite), T2.5 (absence ratchets), T2.5b (Q3)

**Precondition confirmed:** `evidence/live-T2.1-notebook-owner.md` VERDICT
PASS; `reviews/cycle2-programmer-T2.2-T2.3.md` (T2.2/T2.3 production fix)
already in tree.

## T2.4 -- old non-test vs new file

**Old (deleted):** 9 tests, all against a `_MockRepository` that *defined*
`RecordsOC` -- the exact member `IRnResearchNbkRepository` lacks. Never
imported `DataNotebookOperations`. Passed unconditionally regardless of
production behaviour.

**New:** imports `DataNotebookOperations`, calls it live on
`target_sandbox` for `Duplicate`, `Delete`, `GetSubRecords`,
`GetParentRecord`, `GetLocations`/`AddLocation`/`RemoveLocation`, `GetTitle`.
Re-reads every value from the LCM by HVO. Negative coverage: invalid HVO
still raises `FP_ParameterError`; a genuine (monkeypatched) `AttributeError`
propagates unmasked, not laundered.

**New live findings surfaced while writing this (all out of scope, NOT
fixed, reported here for triage):** once T2.2 let `Create()` get past the
#302 crash for the first time ever, three further independent defects
became reachable: (1) `IRnGenericRec.Title` is a bare `ITsString`
(assign directly; no `.get_String`/`.set_String`/`.CopyAlternatives`), and
`IRnGenericRec` has **no `Text` member at all** -- so `Create`,
`CreateSubRecord`, `SetTitle`, `SetContent`, and `Duplicate`'s Title/Text
copy lines all crash; `GetTitle`/`GetContent` silently return `""` instead
(their own try/except swallows the AttributeError). (2) The real names are
`StatusRA`/`TypeRA`/`ConfidenceRA`, not `Status`/`Type`/`Confidence` --
`GetStatus`/`GetRecordType` silently return `None` always; `SetStatus`/
`SetRecordType` write a throwaway Python-side attribute that pythonnet
accepts instead of raising, so the write silently never reaches the LCM.
(3) `DateOfEvent` is CLR-typed `GenDate`, not `System.DateTime` --
`SetDateOfEvent` crashes with `TypeError` on every call. (4)
`Duplicate()`'s (and `GetParentRecord()`'s) sub-record detection --
`isinstance(owner, IRnGenericRec)` on the raw, uncast `.Owner` -- is always
`False` live (pythonnet types `.Owner` as base `ICmObject`), so every
`Duplicate()` call, top-level or sub-record, lands in
`ResearchNotebookOA.RecordsOC`. `Delete()` in the same file already fixed
this exact bug class under #133 via `self._GetTypedOwner`; `Duplicate`/
`GetParentRecord` were never updated to match. The rewritten file routes
around (1) for setup only (raw factory + direct `.Title =`), uses only
genuinely-correct methods for positive coverage, and locks in the current
(buggy) placement for finding (4) as an honest regression test rather than
asserting the originally-intended position.

## T2.5 -- absence ratchets (no production edits)

All five rows (`IRnGenericRec.TextsRC`, `ICmAnthroItem.TextsRC`,
`ILangProject.RecTypesOA`, `ICmPerson.LanguagesRC`,
`ICmBaseAnnotation.RepliesOS`) confirmed absent live. Ruling C2 pinned:
`Singleton` is directly declared; `Count` is inherited from the generic
`IRepository<T>` base and doesn't surface via `GetProperties()` on the
derived interface (a reflection quirk, matching cycle-1's own `test_3a`) --
pinned functionally instead (`hasattr`/real call on `target_sandbox`).

## T2.5b -- Q3

**Q3 ANSWER: no Context-named member exists under any suffix (OA/RA/OS/RS/
bare) on either MoEndoCompound or MoExoCompound -- Catalogue 2 row 25 is
CLEARED.** `compound_rule.py` untouched (ruling C9).

## Counts

`test_datanotebook_duplicate.py`: 6 collected, 6 passed.
`test_lcm_member_truth_sweep.py`: 19 collected, 19 passed (8 new).
Combined: 25/25, `run_mode: live`.
