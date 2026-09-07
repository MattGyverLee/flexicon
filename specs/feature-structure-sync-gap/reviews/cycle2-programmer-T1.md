# Cycle 2 -- Programmer T1: lcm_casting._interface_cache feature-structure entries

## (a) Diff summary -- `flexicon/code/lcm_casting.py`

Added 4 new guarded-import blocks (following the file's existing per-interface
isolation convention) inside `_ensure_interfaces()`, after the `ILangProject`
block: (1) `IPhNCFeatures, IPhNCSegments, IPhPhoneme`; (2) `IPartOfSpeech`
alone; (3) `IPosFeatures` -- **hardcoded to `None`, no import attempt** (see
finding below); (4) `IFsComplexFeature, IFsFeatStruc, IFsComplexValue,
IFsClosedValue`. Did **not** duplicate `MoStemMsa`/`MoDerivAffMsa`/
`MoInflAffMsa`/`MoAffixAllomorph` -- confirmed already present at lines
215-221. Added a registration block (with a D3-referencing comment modeled
on the `ILangProject` precedent) that maps the 9 new ClassNames into
`_interface_cache` via `if X is not None:` guards, noting `PhNCSegments` is
inert here and exists only to unblock spec 233.

## (b) Caller-delta table

| Call site(s) | Receives a table ClassName? | Delta | Downstream risk |
|---|---|---|---|
| 22 `_GetTypedOwner` owner-collection sites: `ConstChartRowOperations:505`, `AllomorphOperations:350/423`, `EtymologyOperations:287/349`, `ExampleOperations:256/318`, `LexReferenceOperations:827`, `LexSenseOperations:276/2004`, `VariantOperations:480/539`, `NoteOperations:259/332`, `ParagraphOperations:248/312`, `SegmentOperations:673/1025`, `WfiMorphBundleOperations:240`, `DataNotebookOperations:384`, `AnthropologyOperations:460` | No -- owners are always `LexEntry`/`LexSense`/`LexRefType`/`DsConstChart`/`RnGenericRec`/`CmPossibility`/`StText`(via `.SegmentsOS`/`.ParagraphsOS`)/`WfiAnalysis`, confirmed by reading each site's owning-collection | None | None |
| `InflectionFeatureOperations.py:492` `_GetTypedOwner(fs)` (the #133 fix) | **Yes** -- `fs.Owner` can be `PhNCFeatures`/`PhPhoneme`/`PartOfSpeech`/`PosFeatures`/`FsComplexFeature` (also the 4 already-cached MSA/allomorph types, `WfiAnalysis`) | Checked literal `FeaturesOA` presence against `tests/contract/snapshots/liblcm_baseline.json`: **only `PhNCFeatures` and `PhPhoneme` have a property literally named `FeaturesOA`.** `PartOfSpeech` has `DefaultFeaturesOA`/`InherFeatValOA` (different names); `FsComplexFeature` has `DefaultOA`, not `FeaturesOA`. So T1 activates the dead `hasattr(parent,"FeaturesOA") and parent.FeaturesOA == fs` branch **only** when the owner ClassName is `PhNCFeatures` or `PhPhoneme`; for `PartOfSpeech`/`PosFeatures`/`FsComplexFeature` owners the branch stays False (correctly) until T11 rewrites this method against the C1 resolver's per-ClassName property map. | FINDING (not fixed in T1): `FeatureStructureDelete` may now actually clear `FeaturesOA` on a `PhNCFeatures`/`PhPhoneme` owner where it previously silently no-op'd. Correct behaviour, needed for #133/T11, but ships as a T1 side effect. No test currently locks it. |
| `lcm_casting.py:501-502` `clone_properties(source,dest)`, called from `PhonemeOperations.py:379` (`source_features`/`new_features`, ClassName `FsFeatStruc`) | Technically yes | None -- `.FeaturesOA` is declared to return `IFsFeatStruc` directly (no subtype), so pythonnet already returns the fully concrete object before any cache lookup; the cast is a no-op both before and after T1 | None |
| Same helper, called from `PhonologicalRuleOperations.py:1400`, `EnvironmentOperations.py:627/639` | No -- `PhRegularRule`/`PhMetathesisRule`/`PhSimpleContextSeg`/`PhSimpleContextNC`, all pre-existing cache entries | None | None |
| `lcm_casting.py:809`, `:882` (`get_common_properties`, `get_concrete_type_properties`) | N/A -- zero callers anywhere in `flexicon/code` (dead utility functions) | None | None |
| `LexSenseOperations.py:1447` `cast_to_concrete(existing_msa)` | No -- MSA ClassNames only, all pre-existing | None | None |
| `InflectionFeatureOperations.py:1559`, `PhonFeatureOperations.py:824/1023`, `catalog_backed.py:495` (all `cast_to_concrete(factory)`) | No -- guarded by `hasattr(factory,"ClassName")`; confirmed live that factory objects (e.g. `IPartOfSpeechFactory` via `POSOperations._get_factory`) expose no `ClassName`, so the cast never fires | None | None |
| `wrapper_base.py:122` `self._concrete = cast_to_concrete(lcm_obj)` | No -- every `LCMObjectWrapper` subclass (`AffixTemplate`, `CompoundRule`, `AdhocProhibition`, `Annotation`, `PhonologicalRule`, `MorphosyntaxAnalysis`, `Allomorph`, `PhonologicalContext`) wraps ClassNames already cached or unrelated to the 9 | None | None |
| Test files: `test_owner_cast_pattern.py` (`_GetTypedOwner(None/_Stub)`, `cast_to_concrete(chart)` where `chart.ClassName=="DsConstChart"`); `test_wrappers.py` (monkeypatches the real function); `test_affix_template_wrappers.py` (`lcm_casting.cast_to_concrete = lambda obj: obj`); `test_allomorphs_live.py`/`test_etymologies_live.py`/`test_variants_live.py` (comment-only references; owners are always `LexEntry`) | No | None | None |

## (c) Newly-activated dead code

1. **`InflectionFeatureOperations.FeatureStructureDelete` (#133 fix)** partially
   activates: live for `PhNCFeatures`/`PhPhoneme` owners, still dead for
   `PartOfSpeech`/`PosFeatures`/`FsComplexFeature` owners (property-name
   mismatch, see table). T11's job to finish.
2. **`IPosFeatures` confirmed absent** from this LCM version by live
   introspection (`tests/contract/test_lcm_contract.py`'s
   `TestLiveContractVerification`, real liblcm assembly scan --
   `missing_types: ["IPosFeatures"]`). Only a descriptive comment at
   `InflectionFeatureOperations.py:486` ever named it; no snapshot/probe/import
   confirms it. Hardcoded to `None` (no import attempt), matching the existing
   `IPhReduplicationRule` precedent, rather than a guarded import that always
   fails.
3. **Pre-existing, unrelated live-test failure**:
   `test_natural_classes.py::TestNaturalClassSync::test_apply_raises_on_type_mismatch_segments_target`
   fails both before and after this change (`git stash` comparison run) --
   `NaturalClassOperations.py:1270` calls `.Name` on a bare `ICmObject` inside
   the mismatch-error branch. Not a T1 regression; not repaired here.

## (d) New test

`tests/operations/test_owner_cast_pattern.py::TestFeatureStructOwnerCastT1::test_cast_to_concrete_resolves_all_nine_owner_classnames`.
Access path: locates a live Hvo per ClassName via `GetAll()`/`FeatureGetAll()`/an
explicit in-file cast (discovery only), then re-fetches via
**`project.Object(hvo)`** (guaranteed bare `ICmObject`, C2) and asserts
`isinstance(cast_to_concrete(base_obj), <interface>)` plus a concrete-only
attribute becomes reachable. 8/9 ClassNames exercised live; `PosFeatures`
skipped (confirmed absent, see (c)).

## (e) Results

Offline: `python -m pytest tests -m "not requires_live_project" -q` ->
**1277 passed, 0 failed**. Live (`FLEXLIBS_REQUIRE_LIVE=1`, real FieldWorks,
`run_mode: live` per `tests/live_status.json`): new T1 test + owner-cast file
4/4 passed; NC/Phoneme suite 34/35 passed (1 pre-existing, unrelated failure,
see (c)); contract suite 22/22 passed after updating
`tests/contract/snapshots/expected_contract.json` for the intentional new
`IFsComplexValue` dependency. Evidence:
`specs/feature-structure-sync-gap/evidence/live-t1-interface-cache.md`.
