# Cycle 1 -- Archaeology report: #296 contract snapshot drift provenance

## Key finding

Commit `4b911d3` (#276) itself says the fix "edited surgically rather than
regenerated: a full regen folds in 9 files of unrelated accumulated drift...
Follow-ups filed as #293, #294, #295, #296, #297, #298" -- that is the direct
origin of #296, and the file list matches the 9 exactly.

## Provenance table

| symbol/file | introducing commit | subject | issue | what it was for |
|---|---|---|---|---|
| `transaction.py` (whole file, new LCM surface) | `287bb20` | fix(transaction): rewrite on UndoableUnitOfWorkHelper; fix Undo/Redo (B1, B3) | #233, #234, #235 | Deleted hand-rolled depth counter; imports `SIL.LCModel.Infrastructure.UndoableUnitOfWorkHelper`, reads `ActionHandlerAccessor.CurrentDepth` |
| `transaction.py` -- `.set_RollBack()` | `fe42ddf` | feat(write-path): AbortSession (A3), CAPABILITIES (B4), D9 set_RollBack fix | (spec D9, no GH #) | pythonnet gives no property for `RollBack` (private getter); `.RollBack=` was silently discarding writes -- switched to `set_RollBack(...)` |
| `undoable_operation.py` (whole file, new LCM surface) | `287bb20` | fix(transaction): rewrite on UndoableUnitOfWorkHelper... | #233 | `_FLExUndoableOperation` now constructs `UndoableUnitOfWorkHelper` directly instead of the broken 1-arg `BeginUndoTask` discovery |
| `BaseOperations.py` -- `IFsClosedValue/Factory`, `IFsComplexValue/Factory`, `IFsFeatStruc/Factory` | `cfc86af` | feat(base-operations): add feature-structure owner resolver and recursive serializer | none (specs/feature-structure-sync-gap T2/T3) | shared `_ResolveFeatureStrucOwner` / `_GetFeatureStruc` helpers; further generalized by `4aca74a` (T4) and `6643b48` (T5) |
| `FLExProject.py` -- `FwTextPropType`+`ktptObjData`, `TsStringUtils.MakePropsBldr`/`MakeStrBldr` | `f60137b` | fix(272): migrate every raw ServiceLocator.GetInstance site off the dead call | #272 | replaced raw `ServiceLocator.GetInstance<T>()` calls with proper builder/text-prop APIs |
| `FLExProject.py` -- `LexEntryRefTags`+`krtComplexForm` | `03593c7` | fix(272): repair the rest of the complex-form write path found by live verification | #272 | correct complex-form `LexEntryRef` creation via the real ref-type tag |
| `FLExInit.py` -- `Sldr.IsInitialized` | `34a2816` | fix(FLExInit): stop swallowing genuine Sldr.Initialize failures | closes #249 | probe before `Initialize()`/`Cleanup()` to stop mis-swallowed exceptions and a `.ldml.bad` corruption loop |
| `Grammar/NaturalClassOperations.py` -- `IFsFeatStruc` family | `8a6c3ab` | fix(natural-class): stop silently dropping FeaturesOA on cross-project sync | none (same bug class as #222) | capture/restore FeaturesOA on `IPhNCFeatures` sync; generalized later by `4aca74a`/`6643b48` |
| `Lexicon/AllomorphOperations.py` -- `IMoStemAllomorph`/`IMoAffixAllomorph` | `df37e35` (introduced), `ef3bd4e` (contract-conformance fix) | feat(feature-structure-sync-gap) T8 / fix(260-environment-resolver-cast) | #260 | cast environment-object results to concrete allomorph interfaces instead of bare `IMoForm` |
| `TextsWords/WfiMorphBundleOperations.py` -- `IMoForm` | `cfbfd43` | fix(morph-bundle)!: GetMorphType returned the allomorph, not the morph type | none cited | fixed `GetMorphType` to resolve the real `IMoMorphType`/`IMoForm` chain |
| `lcm_casting.py` -- batch of concrete interfaces (`ICmAnnotationDefn`, `ICmLocation`, `ICmPerson`, `ICmSemanticDomain`, `IConstChart*`, `IFsFeatStruc`, `ILexEntryType`, `IPartOfSpeech`, `IPhNCFeatures/Segments/Phoneme`, etc.) | `cae158b` (primary); contributions from `3da12cf`, `1790fcc`, `4825466` | fix(270): cast collection elements to their concrete LCM interfaces | #270 (also #271) | `cast_to_concrete` sweep so collection wrappers return concrete LCM interfaces, not base `ICmObject` |
| `TsStringUtils.MakePropsBldr`/`MakeStrBldr` (global `type_usage`, call site) | `f60137b` | fix(272): migrate every raw ServiceLocator.GetInstance site off the dead call | #272 | call sites live in `FLExProject.py` |
| `Sldr.IsInitialized` (global `type_usage`, call site) | `34a2816` | fix(FLExInit): stop swallowing genuine Sldr.Initialize failures | closes #249 | call site lives in `FLExInit.py` |
| `FwTextPropType.ktptObjData` (global `type_usage`, call site) | `f60137b` | fix(272): migrate every raw ServiceLocator.GetInstance site off the dead call | #272 | call site lives in `FLExProject.py` |

All 9 files plus the 3 `type_usage` entries were traced to a specific commit
via `git log -S` on the introduced symbol, cross-checked against the actual
added lines in each diff. Nothing here is a guess.

## Note on a stray in-progress regen

At the time this investigation ran, the working tree had an uncommitted
modified `expected_contract.json` that looked like a prior WIP regen
capturing this same drift. That file was later found to have been reverted
back to `HEAD` content by activity from another concurrent local session
(unrelated to this investigation) before the final regen+commit for #296.
See the programmer's cycle-1 report for the determinism/gate verification
that was subsequently redone under a file lock.
