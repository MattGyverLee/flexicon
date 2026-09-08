# Cycle 13 programmer report -- T7 (POSOperations feature-struct sync, #252)

## 1. Predictions P1-P5

**P1 -- HELD.** `GetSyncableProperties(hvo=2706)` at unmodified HEAD returned
`{}` (0/4 keys); the same call via a typed object returned all four
(`Name`/`Abbreviation`/`Description`/`CatalogSourceId`). #252 is a coverage
gap PLUS a pre-existing silent-drop bug on the HVO entry path, not a pure
coverage gap. Evidence: `evidence/live-T7.md` STEP 0.

**P2 -- HELD.** The `__ResolveObject` cast (cast to `IPartOfSpeech` on
`ClassName == "PartOfSpeech"`, unchanged otherwise) changed nothing outside
`test_issue252_pos_feature_sync.py`: the full offline comparator (STEP 5)
shows zero pass/fail change to any pre-existing test, and the same 2
pre-existing foreign failures as before.

**P3 -- HELD.** Both `DefaultFeaturesOA`/`InherFeatValOA` exist on
`IPartOfSpeech`, declared `IFsFeatStruc`; 0/5 sandbox POS carry a non-null
struct for either. The live round-trip tests create their structs via
`_ApplyFeatureStruc` before reading. (Sandbox held 5 POS this run vs
cycle-1's 26 -- a snapshot difference, not a contradiction of P3's
existence/type/null claims.)

**P4 -- HELD.** `_ResolveFeatureStrucOwner(pos_obj)` with no `slot=` raised
`FP_ParameterError` naming both `"PartOfSpeech"` and `"slot"`; a fresh
re-fetch confirmed no partial attach (`DefaultFeaturesOA`/`InherFeatValOA`
both still `None`).

**P5 -- HELD, split confirmed exactly.** Removing the `__ResolveObject`
cast (mutation M1) killed the direct cast test AND
`test_hvo_entry_path_captures_name` (the HVO-entry Name-capture test), while
both feature-struct-key round-trip tests, the C7-raise test, and the
slot-ambiguity test all SURVIVED -- because they either route through
`_ResolveFeatureStrucOwner`'s own internal cast (a second compensating
layer) or never touch `__ResolveObject` for an already-typed object.

## 2. Commit hashes

- Production: `4e9d152` -- `flexicon/code/Grammar/POSOperations.py`
- Tests: `4b746a0` -- `tests/operations/test_issue252_pos_feature_sync.py`
- Evidence: `0fefa00` -- `specs/feature-structure-sync-gap/evidence/live-T7.md`
- CHANGELOG: `3eff177` -- `CHANGELOG.md`

`.pyi` untouched: `GetSyncableProperties`/`ApplySyncableProperties` were not
previously declared there and no signature changed.

## 3. Mutation table

| # | Mutation | Killed | Survived | Restore verified |
|---|---|---|---|---|
| M1 | `__ResolveObject` cast removed | offline cast-shape test; live: direct-cast test, HVO-entry-Name test | live: both slot round-trips, C7-raise, slot-ambiguity | hash `f94b4d97...` |
| M2 | presence gate -> truthiness | offline: source-shape lock + both falsy-but-present tests | offline: guid-only-truthy, neither-present (same T6b finding: truthy fixtures can't separate presence from truthiness) | hash `f94b4d97...` |
| M3 | `on_unresolved` raise->skip | offline propagation test; live C7-raise test | -- | hash `f94b4d97...` |
| M4 | ambiguous-no-slot picks `rows[0]` (`BaseOperations.py`) | live slot-ambiguity test | -- (T14a's MoDerivAffMsa raise test would also die under this shared-code mutation; not re-run, noted only) | hash `a8e914bf...` |
| M5 | InherFeatVal calls forced to `slot="Default"` | offline both-slots tests; live InherFeatVal round-trip | live Default round-trip (only Default populated, so mis-routing is invisible to it) | hash `f94b4d97...` |

All five run in one disposable `git worktree add <tmpdir> HEAD` (from
`4b746a0`), Target `.fwbackup` copied read-only in. Each mutation reverted
and `git hash-object` re-verified before the next; final full offline run
in the worktree (20 passed, 6 deselected) before `git worktree remove
--force`. Shared tree's `git diff --stat` stayed empty throughout.

## 4. Comparator delta

```
BEFORE (worktree @ 1d88aa4, pre-T7): 2 failed, 396 passed, 512 deselected
AFTER  (shared tree @ 4b746a0):      2 failed, 416 passed, 518 deselected
```

Delta: +20 passed (exactly the new file's offline tests), +6 deselected
(exactly its live tests), failed unchanged at 2 -- the same
`TestPhase2JoinOrOpen` pair, same messages. Matches the "exactly 2, not 3,
not the old 392" expectation.

## 5. Line-number drift

None against the dispatch's anchors. `GetSyncableProperties` at :1124,
`ApplySyncableProperties` at :1178, `__ResolveObject` at :1107, all 15
`__ResolveObject` call sites at the listed lines (verified by grep before
editing), `FEATURE_STRUC_OWNER_TABLE`'s `"PartOfSpeech"` row at :127-130 --
all confirmed exact.

## 6. Chosen not to fix, and why

- **GUID-string support in `__ResolveObject`** (lead ruling 2): a `str`
  falls through unresolved, returned unchanged. Pinned by a dedicated
  offline test. Folded into T12 per instruction.
- **Pre-existing `hasattr` gates** on Name/Abbreviation/Description/
  CatalogSourceId (lead ruling 3): kept, now redundant but harmless once
  the cast lands. Allowlisted in the AST test rather than removed.
- **`CompareTo` behaviour change** (pre-ruling 4): not modified, but its
  output changed as a side effect -- two POS with identical feature specs
  and different struct GUIDs now report a difference on the `<key>Guid`
  key (previously invisible to `CompareTo`, since the keys didn't exist).
  Pinned by `TestPOSSyncCompareToStructGuidPinning`. Candidate follow-up:
  compare by serialized spec content rather than struct identity, so two
  POS with byte-identical feature values but independently-created structs
  read as equal. Not filed as an issue per instruction -- noted here only.
- **T14a's own ambiguous-owner test** was not re-run under M4 (out of this
  file's scope); noted in the mutation table as an expected co-kill under
  the same shared-code mutation, not independently verified this cycle.
