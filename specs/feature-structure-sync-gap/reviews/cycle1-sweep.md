# Cycle-1 sweep -- feature-structure sync gap (#251 / #252 / #256)

Agent: Explore
Feature: specs/feature-structure-sync-gap
Scope: static audit, read-only.

> NOTE: dispatched in strict read-only mode with no Write/Edit tools; this report
> was persisted verbatim by the main session on the agent's behalf.

**Method.** Inverted as instructed. Source of truth for "which LCM types own a
feature structure" is the live-reflected type snapshot
`tests/contract/snapshots/liblcm_baseline.json` (255 types, `metadata.generated_at`
2026-08-13), queried for every property matching `Feat.*(OA|OC|OS|RA|RC)$`.
`api_usage_extract.json` / `api_usage_by_namespace.json` turned out to record
**imports only** (`{file, namespace, class, line_start, import_type, statement}`)
-- no property-level usage -- so they cannot confirm or deny capture; the snapshot
replaced them. `docs/API_ISSUES_CATEGORIZED.md` Category 8 covers `Source` /
`BaselineText` only; it has **no** feature-structure entry (worth adding).

Four types are in neither snapshot (`liblcm_baseline.json`, `liblcm_unknown.json`)
and have zero references in `flexicon/code/`: `IMoDerivStepMsa`,
`ILexEntryInflType`, `IMoStemName`, `IFsComplexValue`. Their properties are marked
**UNCONFIRMED**.

## DELIVERABLE 1 -- coverage table

| LCM owning type | feature-struct property | Operations class | captured? | prio |
|---|---|---|---|---|
| `IMoStemMsa` | `MsFeaturesOA` (confirmed) | `Lexicon/MSAOperations.py` | **NO** -- class has zero sync methods | P0 |
| `IMoInflAffMsa` | `InflFeatsOA` (confirmed) | `Lexicon/MSAOperations.py` | **NO** -- named only in `ChangeAffixVariant` lost-fields (`:538-539`) | P0 |
| `IMoDerivAffMsa` | `FromMsFeaturesOA`, `ToMsFeaturesOA` (confirmed) | `Lexicon/MSAOperations.py` | **NO** | P0 |
| `IPartOfSpeech` | `DefaultFeaturesOA`, `InherFeatValOA` (confirmed) | `Grammar/POSOperations.py` | **NO** -- `Get`:1124 emits Name/Abbreviation/Description/CatalogSourceId; `Apply`:1178 is a pure `super()` delegate. `"POS"` is a live sync object type (`flexicon/sync/engine.py:445`) | P0 |
| `IMoAffixAllomorph` | `MsEnvFeaturesOA` (confirmed) | `Lexicon/AllomorphOperations.py` | **NO** -- `Get`:487 emits Form/IsAbstract/MorphTypeRA only; no `Apply` override. `"Allomorph"` is a live sync type (`engine.py:441`) | P0 |
| `IPhPhoneme` | `FeaturesOA` (confirmed) | `Grammar/PhonemeOperations.py` | **PARTIAL** -- captured at `Get`:1351, but `Apply` gate `:1431` is truthiness (D2-P0) and struct GUID is not preserved (`:1471` plain `factory.Create()` vs NC's `_CreateWithGuid`) | P0/P1 |
| `IPhNCFeatures` | `FeaturesOA` (confirmed) | `Grammar/NaturalClassOperations.py` | **YES** -- reference template (1039 / 1169 / 1284) | -- |
| `IWfiAnalysis` | `MsFeaturesOA` (confirmed) | `TextsWords/WfiAnalysisOperations.py` | **NO** -- `Get`:335 emits `CategoryRA` only | P1 |
| `IFsFeatStruc` | `FeatureDisjunctionsOC` (nested structs, confirmed) | Infl/PhonFeature/NC/Phoneme | **NO** -- every reader walks `FeatureSpecsOC` only | P1 |
| `IFsComplexValue` | `ValueOA` (nested `IFsFeatStruc`) -- **UNCONFIRMED** | none | **NO** -- `PhonemeOperations.py:1358-1364` explicitly `continue`s any non-`IFsClosedValue` spec; NC:1144 same | P1 |
| `ICmBaseAnnotation` | `FeaturesOA` (confirmed) | `Notebook/NoteOperations.py` | **NO** -- `Get`:420 emits Comment/Source/AnnotationType/BeginObject | P2 |
| `IScrScriptureNote` | `FeaturesOA` (confirmed, inherited) | `Scripture/ScrNoteOperations.py`, `ScrAnnotationsOperations.py` | **NO** -- neither file defines `GetSyncableProperties` | P2 |
| `IMoDerivStepMsa` | `MsFeaturesOA`/`InflFeatsOA` -- **UNCONFIRMED** | none | **N-A** -- no wrapper, zero references | -- |
| `ILexEntryInflType` | `InflFeatsOA` -- **UNCONFIRMED** | none | **N-A** -- only reached as `InflTypeRA` (`WfiMorphBundleOperations.py:1156`) | -- |
| `IMoStemName` | `RegionsOC` (collection of `IFsFeatStruc`) -- **UNCONFIRMED** | none | **N-A** | -- |
| `IFsFeatStrucType` | feature TYPES | `Grammar/GramCatOperations.py` | **N-A** -- established false positive | -- |
| `ILangProject` | `MsFeatureSystemOA`, `PhFeatureSystemOA` | Infl/PhonFeatureOperations | **N-A** -- `IFsFeatureSystem`, not `IFsFeatStruc` | -- |
| `IPhSimpleContextNC` / `IPhSimpleContextSeg` | `FeatureStructureRA` | `PhonologicalRuleOperations.py:1215-1249` | **N-A** -- despite the name these are *references* to `IPhNaturalClass` / `IPhPhoneme`. New false-positive class; document it | P2 |
| `IFsClosedValue` / `IPhFeatureConstraint` | `FeatureRA` | Phoneme/NC/PhonRule | **N-A** -- reference to `IFsFeatDefn` | -- |

## DELIVERABLE 2 -- truthiness-vs-presence gate audit

Every `ApplySyncableProperties` in `flexicon/code/` (15 definitions):

| file:line | gate | verdict |
|---|---|---|
| `Grammar/PhonemeOperations.py:1431` | `if features:` | **P0 -- BUG.** Identical to the shape 3abf6b5 fixed. `Get`:1353 emits `FeaturesGuid` whenever `FeaturesOA` is non-null, but `:1372` `if specs:` omits `"Features"` for an empty struct. Empty-but-present `FeaturesOA` -> falsy -> `__ApplyFeatures` never runs -> target `FeaturesOA` stays null. Fix: `if "Features" in props or "FeaturesGuid" in props:` and pass `features or []` + the guid, mirroring `NaturalClassOperations.py:1257`. |
| `Grammar/NaturalClassOperations.py:1257` | `if features or features_guid:` | OK -- the 3abf6b5 fix. |
| `Grammar/PhonemeOperations.py:1428` | `isinstance(basic_ipa, dict) and basic_ipa` | P2 -- truthiness on a dict; benign today (`Get`:1341 omits empty), same latent shape. |
| `Grammar/PhonFeatureOperations.py:760` | `if values:` | P2 -- truthiness on a list; benign today (`Get`:709 omits empty), same latent shape. |
| `Lexicon/EtymologyOperations.py:548` | `if not guid_str: continue` | P2 -- key-present-with-`None` never clears the target RA. Undocumented no-clear-on-null policy. |
| `Lexicon/ExampleOperations.py:470, 481` | `if "Reference" in ...`, `if "TranslationsOC" in ...` | OK -- presence. |
| `Lexicon/LexSenseOperations.py:755` | `if field_name not in special_props: continue` | OK -- presence. |
| `Lexicon/LexEntryOperations.py:655` | iterates `rc_props.items()` | OK -- presence (empty frozenset honoured as a real value; ruling documented at :656-658). |
| `BaseOperations.py:1236` | -- | see structural note below. |
| Pure `super()` delegates, no gates: `GramCatOperations.py:648`, `POSOperations.py:1178`, `MorphRuleOperations.py:944`, `PhonologicalRuleOperations.py:1497`, `StratumOperations.py:306`, `InflectionFeatureOperations.py:1713`, `EnvironmentOperations.py:719` | | OK |

**Structural note (P1) for the new work:** `BaseOperations._apply_props_loop`
(`BaseOperations.py:346-353`) dispatches on `isinstance(value, dict)` -> **any**
dict is treated as a multi-WS multistring. A feature-struct value emitted as a
dict would be routed to `getattr(item, prop_name)` and dropped silently at
`:352-353`. New MSA/POS keys **must** be popped out of `props` before `super()`,
exactly as NC:1233 and Phoneme:1421 do.

## DELIVERABLE 3 -- hasattr-on-subclass-member audit

Resolvers confirmed base-typed: `FLExProject.Object` (`FLExProject.py:3212-3226`)
returns `ServiceLocator.GetObject(hvo)` -- a bare `ICmObject`.
`NaturalClassOperations.__GetNaturalClassObject` (:106-118) and
`PhonemeOperations.__GetPhonemeObject` (:1263-1275) both pass HVOs straight
through it and return objects unchanged. `PhonologicalDataOA.NaturalClassesOS`
yields base `IPhNaturalClass`, so NC sites are dead on **both** input paths.

| file:line | gate | fix |
|---|---|---|
| `Grammar/NaturalClassOperations.py:911`, `:913` (`GetType`) | `hasattr(nc,"FeaturesOA")` / `"SegmentsRC"` | **P1 dead code** -- always False; falls through to the `nc.ClassName` "defensive fallback", which accidentally masks the bug. Discriminate on `ClassName == "PhNCFeatures"` / `"PhNCSegments"`. |
| `Grammar/NaturalClassOperations.py:956` (`GetFeatures`) | `if not hasattr(nc,"FeaturesOA")` | **P1 wrong behaviour** -- raises a spurious "is not feature-based" `FP_ParameterError` for every genuine `PhNCFeatures`. Fix: `if nc.ClassName != "PhNCFeatures": raise` then `IPhNCFeatures(nc).FeaturesOA` -- the pattern already present in the same file at `:1258-1270`. |
| `Grammar/NaturalClassOperations.py:1021` (`SetFeatures`) | same | same fix; currently `SetFeatures` is inert for its primary call pattern. |
| `Grammar/NaturalClassOperations.py:655`, `:711`, `:766` | `hasattr(nc,"SegmentsRC")` | **P1** -- `GetPhonemes` returns `[]`, `AddPhoneme`/`RemovePhoneme` reject every segment-based class. Cast via `IPhNCSegments`. |
| `Grammar/PhonemeOperations.py:1351` (`GetSyncableProperties`) | `hasattr(phoneme,"FeaturesOA") and phoneme.FeaturesOA` | **P0 silent data loss on the HVO/GUID path** -- `FeaturesOA` is on `IPhPhoneme` itself, so this works when the caller passes an object out of `PhonemesOC`, but on an HVO/GUID input the phoneme is `ICmObject`-typed and **both** `Features` and `FeaturesGuid` are silently omitted. Fix: `IPhPhoneme(...)` cast inside `__GetPhonemeObject`. |
| `Grammar/PhonemeOperations.py:1167` (`GetFeatures`), `:1237`, `:366` (`Duplicate`) | same | same one-line resolver fix covers all three. |
| `Grammar/InflectionFeatureOperations.py:1031` (`MakeFeatStruc`) -- known instance | `if not hasattr(owner_unwrapped,"FeaturesOA")` | **P0 -- this is #251/#252/#256 in its purest form.** `FeaturesOA` does not exist on **any** MSA type, nor on `IPartOfSpeech` (snapshot: `DefaultFeaturesOA`/`InherFeatValOA`), yet the docstring at `:1012` instructs callers to `Pass owner=msa`. So the documented contract is unreachable by construction, and a base-typed genuine `IPhNCFeatures` owner raises spuriously. Fix: an `owner.ClassName` -> property-name resolver (`MoStemMsa`->`MsFeaturesOA`, `MoInflAffMsa`->`InflFeatsOA`, `MoDerivAffMsa`->`From-`/`ToMsFeaturesOA`, `PartOfSpeech`->`DefaultFeaturesOA`/`InherFeatValOA`, `PhNCFeatures`/`PhPhoneme`->`FeaturesOA`, `MoAffixAllomorph`->`MsEnvFeaturesOA`) plus a cast, then `setattr`. This resolver **is** the central artefact this whole feature needs. |
| `Grammar/PhonFeatureOperations.py:614` (`MakeFeatStruc`) | same | Byte-for-byte clone of `:1031`. Must be fixed with the same resolver, not independently. |
| `Grammar/InflectionFeatureOperations.py:493` (`FeatureStructureDelete`) | `hasattr(parent,"FeaturesOA")` after `_GetTypedOwner(fs)` | **P1 -- the #133 fix is incomplete.** `_GetTypedOwner` (`BaseOperations.py:1564-1602`) delegates to `cast_to_concrete`, which returns the object **unchanged** for any `ClassName` absent from `_interface_cache` (`lcm_casting.py:213-295`). That cache has **no** entry for `PosFeatures`, `FsComplexFeature`, `PhNCFeatures`, `PhNCSegments`, `PhPhoneme`, `PartOfSpeech`, or any feature-struct owner. So `Delete` still silently does nothing for exactly the owners its own comment at `:485-486` names. Also needs the varying property name. |

**Enabling defect (P1, one place, fixes several rows):**
`lcm_casting._interface_cache` is missing every feature-structure owner class.
Adding `PhNCFeatures`, `PhNCSegments`, `PhPhoneme`, `PartOfSpeech`, `PosFeatures`,
`FsComplexFeature` there makes `_GetTypedOwner` and `cast_to_concrete` work for all
of the above.

**Do not double-file:** `AllomorphOperations` `PhoneEnvRC` x4,
`LexEntryOperations.py:433`, and `PhonologicalRuleOperations` `RightHandSidesOS` x4
are the same defect family but are already scoped in
`specs/233-basetype-cast-sweep/spec.md` section 2. `Lexicon/allomorph.py:193/276`
and `Grammar/phonological_rule.py` gate on `self._concrete` (already
`cast_to_concrete`d) -- genuine OK. `Lexicon/EtymologyOperations.py:478/491`
(`LanguageRA`, `LanguageNotesRA`) are dead but for a different reason -- the members
do not exist at all; deliberately unfixed per
`docs/API_ISSUES_CATEGORIZED.md:466-473`.

## DELIVERABLE 4 -- shared-helper question: **YES, one helper. Fold #253 in.**

`NaturalClassOperations.__ApplyFeatures` (`:1282-1397`) and
`PhonemeOperations.__ApplyFeatures` (`:1454-1521`) are line-for-line the same
algorithm. Identical in both: the ownership-first `struct is None` create bracket;
the `existing_pairs` idempotency set built by `IFsClosedValue(raw)` over
`struct.FeatureSpecsOC` with the same `try/except: continue`; the
`IFsFeatStruc(struct)` re-fetch; the `(feat_guid.lower(), val_guid.lower())` skip;
the `IFsClosedValueFactory` create -> `FeatureSpecsOC.Add` -> `FeatureRA`/`ValueRA`
write inside a `_TransactionCM`; and the "guards stay outside the transaction so no
empty named undo entry is created" rule. `__ResolveByGuid` is duplicated verbatim
in both files.

They differ on exactly four axes, **all of them parameters, none of them
structure**:

1. **Owning property name** -- `nc.FeaturesOA` vs `phoneme.FeaturesOA`. Today the
   same string; for MSA/POS it varies (`MsFeaturesOA` / `InflFeatsOA` /
   `From-`/`ToMsFeaturesOA` / `DefaultFeaturesOA` / `InherFeatValOA`). This is
   precisely the axis #251/#252/#256 need, so a `prop_name` parameter is not
   speculative generality -- it is the fix.
2. **Unresolved-GUID policy** -- NC raises `FP_ParameterError` (:1370-1391);
   Phoneme `continue`s (:1510-1513). This is #253, and it is a one-parameter
   difference (`on_unresolved="raise"|"skip"`).
3. **Struct-creation identity** -- NC uses
   `self._CreateWithGuid(factory, guid=features_guid, ...)`; Phoneme uses bare
   `factory.Create()`, losing the source struct's GUID. Phoneme is simply behind;
   the helper should always take the guid.
4. **Diagnostic label** -- NC reads `nc.Name` for messages; Phoneme has none. A
   `label` string parameter.

Two secondary divergences the helper also collapses: Phoneme adds to
`existing_pairs` after insert (`:1521`) and NC does not, so NC double-inserts a
spec repeated twice within one call (P2); and Phoneme's
`__ApplyFeatures(self, item, specs, fill_gaps)` never reads `fill_gaps` -- dead
parameter (P2).

**Recommendation.** Add
`_ApplyFeatureStruc(owner, prop_name, specs, features_guid=None, on_unresolved="raise", label=None)`
to `BaseOperations` -- which already hosts `_CreateWithGuid` (`:1884`),
`_TransactionCM`, and `_GetTypedOwner`, and which NC, Phoneme, MSA and POS all
inherit -- plus one shared `_ResolveByGuid`. Have `NaturalClassOperations` pass
`on_unresolved="raise"` and `PhonemeOperations` pass its current `"skip"`, so the
refactor is behaviour-preserving; then #253 becomes a one-line decision about the
default rather than a rewrite. Three separate implementations are **not**
structurally required. Do **not** unify the policy silently as part of the
refactor -- NC's raise is a deliberate documented domain ruling (`:1294-1299`) and
Phoneme's skip is a documented contract (`:1400-1401`); changing either is a
visible behaviour change that deserves its own note in the spec.

## Priority summary

- **P0 (silent data loss):** MSA x4 properties (no sync methods at all); POS
  `DefaultFeaturesOA`/`InherFeatValOA`; `IMoAffixAllomorph.MsEnvFeaturesOA` -- all
  three reachable through the shipped sync engine; `PhonemeOperations.py:1431`
  truthiness gate; `PhonemeOperations.py:1351` on the HVO path;
  `InflectionFeatureOperations.py:1031` + `PhonFeatureOperations.py:614`
  (documented `owner=msa` contract unreachable).
- **P1:** NC `hasattr` gates x7; `lcm_casting._interface_cache` missing every
  feature-struct owner; `InflectionFeatureOperations.py:493`;
  `IWfiAnalysis.MsFeaturesOA`; `FeatureDisjunctionsOC` / `IFsComplexValue.ValueOA`
  never traversed; phoneme struct-GUID not preserved; `_apply_props_loop`
  dict-dispatch hazard.
- **P2:** annotation/ScrNote `FeaturesOA`; latent truthiness gates at
  `PhonemeOperations.py:1428` and `PhonFeatureOperations.py:760`;
  `EtymologyOperations.py:548`; NC in-call duplicate spec; Phoneme dead
  `fill_gaps`; missing Category-8 doc entry for the varying feature-structure
  property name; `FeatureStructureRA` documented as a false-positive class.
