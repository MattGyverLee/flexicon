# Issue #449: sweep for wrapper values reaching resolvers (cycle 1)

Source: Explore agent, read-only static sweep (not run live). Paths relative to `flexicon/code`.

## Background facts

- Only 4 Operations classes create wrappers:
  - `AllomorphOperations.GetAll` -> `Allomorph`
  - `MSAOperations.GetAll` -> `MorphosyntaxAnalysis`
  - `MorphRuleOperations`: `GetAll`, `GetAllCompoundRules`, `GetAllAffixTemplates`, `GetAllAffixTemplatesForPOS` -> `CompoundRule` / `AffixTemplate`
  - `PhonologicalRuleOperations.GetAll` -> `PhonologicalRule`
- No Operations method returns `AdhocProhibition` or `Annotation` (`GetAllAdhocCoProhibitions` yields raw). `PhonologicalContext` only via `PhonologicalRule.contexts`. `PythonicWrapper` only from user `wrap()`; has `_obj`, no `_concrete`.
- `LCMObjectWrapper` defines no `__eq__` and no `__setattr__`: `raw == wrapper` is always False; `wrapper.XxxRA = v` silently sets a Python attribute.
- `cast_to_concrete(wrapper)` never raises; returns the wrapper unchanged.

## Table 1: where a wrapper reaches a failing operation

| file:line | function | input can be wrapper? | failing operation | already unwraps? |
|---|---|---|---|---|
| Lexicon/AllomorphOperations.py:1595/1597 | `__GetAllomorphObject` (shared by Delete, Duplicate, Get/ApplySyncableProperties, CompareTo, GetForm, SetForm, Set/GetFormAudio, Get/SetMorphType, GetPhoneEnv, Add/RemovePhoneEnv, GetOwningEntry) | Y: items from `GetAll()` | `IMoStemAllomorph(obj)` / `IMoAffixAllomorph(obj)` TypeError | N |
| FLExProject.py:5558-5559 | `LexiconGetAllomorphForms` | Y: loops `self.Allomorphs.GetAll(entry)` internally | `GetForm(wrapper)` TypeError. Fails today with no user input. | N |
| Lexicon/MSAOperations.py:709/712/715 (686, 835) | `ChangeAffixVariant(msa, ...)` | Y: no resolver | `IMoInflAffMsa(msa)` etc. TypeError; `MorphoSyntaxAnalysesOC.Remove(msa)` too. HVO also fails (`msa.ClassName`). | N |
| Lexicon/MSAOperations.py:1295 | `__GetMsaObject` | Y | concrete MSA casts | Y (`._obj`) |
| Grammar/MorphRuleOperations.py:568 | `Delete` (compound) | Y | `CompoundRulesOS.Remove(wrapper)` TypeError | N |
| Grammar/MorphRuleOperations.py:571-574 | `Delete` (template) | Y | `_GetObject(rule.Owner.Hvo)` bare ICmObject -> `hasattr(AffixTemplatesOS)` False -> nothing deleted. Separate bug (raw too). | N |
| Grammar/MorphRuleOperations.py:966 | `__DuplicateCompoundRule` | Y | `CompoundRulesOS.IndexOf(wrapper)` TypeError | N |
| Grammar/MorphRuleOperations.py:983-986 | `__DuplicateAffixTemplate` | Y | `IndexOf(wrapper)`; bare owner -> AttributeError (separate bug) | N |
| Grammar/MorphRuleOperations.py:786 | `SetStratum` | Y | `rule.StratumRA = ...` silent no-op on wrapper | N |
| Grammar/MorphRuleOperations.py:856 | `SetDisabled` | Y | `rule.Disabled = ...` silent no-op | N |
| Grammar/MorphRuleOperations.py:1107 | `__ResolveObject` | Y | feeds all MorphRule rows above | N (only casts PartOfSpeech) |
| Grammar/PhonologicalRuleOperations.py:1413 | `__ResolveObject` | Y | `PhonRulesOS.Remove` / `IndexOf` | Y (needs `_obj` and `_concrete`; PythonicWrapper not unwrapped) |
| BaseOperations.py:837/934/1020 | `MoveUp` / `MoveDown` / `MoveToIndex` | Y | `sequence[i] == item` never True -> ValueError "Item not found" | N |
| BaseOperations.py:1102-1104, 1178-1180, 1254-1256, 3125-3127 | `MoveBefore` / `MoveAfter` / `Swap` / `_FindCommonSequence` | Y | same equality problem | N |
| BaseOperations.py:1674 | `_GetObject` | Y | returns wrapper unchanged | N |
| TextsWords/WfiMorphBundleOperations.py:1054 | `SetMorph` / `__GetMorphObject` | Y: `Allomorph` | `cast_to_concrete` returns wrapper, `isinstance(IMoForm)` fails -> FP_ParameterError | N |
| TextsWords/WfiMorphBundleOperations.py:1157 | `SetMSA` / `__GetMSAObject` | Y: `MorphosyntaxAnalysis` | `bundle.MsaRA = wrapper` TypeError | N |
| Lexicon/LexSenseOperations.py:1668 | `SetGrammaticalInfo(sense, msa)` | Y | `sense.MorphoSyntaxAnalysisRA = wrapper` TypeError | N |

Checked and fine: MorphRuleOperations `GetName`, `SetName`, `Get/SetDescription`, `GetStratum`, `IsDisabled`, `GetSyncableProperties`, `AddSlotToTemplate` (attribute reads only). `PhonologicalRuleOperations.WireRule` / `__PopulateSimpleContext` unwrap via `__ResolveLcmObject`.

## Table 2: private resolvers

Already unwrap:
- `MSAOperations`: `__GetMsaObject`, `__ResolveSense`, `__Resolve`, `__ResolveEntry`
- `PhonologicalRuleOperations`: `__ResolveObject`, `__ResolveFeature`, `__ResolveLcmObject`
- `PhonFeatureOperations.__Unwrap`, `InflectionFeatureOperations.__Unwrap`
- `BaseOperations`: `_ResolveFeatureStrucOwner` (1894), `__ResolveFeatStrucOperand` (2869/2889)

Do not unwrap, can receive a wrapper type (fix):
- `AllomorphOperations.__GetAllomorphObject`
- `MorphRuleOperations.__ResolveObject`
- `BaseOperations._GetObject`
- `WfiMorphBundleOperations.__GetMorphObject`, `__GetMSAObject`

Do not unwrap, only reachable with a `PythonicWrapper` (low risk): AllomorphOperations `__GetEntryObject`/`__GetEnvironmentObject`; PhonFeatureOperations `__ResolveObject`; InflectionFeatureOperations resolvers; PhonologicalRuleOperations `__ResolveBoundary`; Environment/POS/Stratum/LexEntry/SemanticDomain/Location/Person/ReversalIndex/ReversalIndexEntry/Scr* resolvers; ConstChart*; NaturalClass, Phoneme; Etymology, Example, LexSense, Pronunciation, Variant; LexReference (4), Overlay (2), PossibilityList (2); possibility_item_base; Anthropology, DataNotebook, Check; Discourse (3), Paragraph (2), Segment (3), Text; WfiAnalysis (3), WfiGloss; WfiMorphBundle bundle/analysis/sense/inflection-class resolvers.

## GetAll docstrings that should mention `.lcm_object` (none do today)

- `Lexicon/AllomorphOperations.py:135` `GetAll`
- `Lexicon/MSAOperations.py:177` `GetAll`
- `Grammar/MorphRuleOperations.py:142` `GetAll` (Returns line is wrong: says `IMoCompoundRule | IMoInflAffixTemplate`, yields wrappers)
- `Grammar/MorphRuleOperations.py:170/201/239` `GetAllCompoundRules`, `GetAllAffixTemplates`, `GetAllAffixTemplatesForPOS`
- `Grammar/PhonologicalRuleOperations.py:105` `GetAll`
- `FLExProject.py:5271` `LexiconAllAllomorphs`

## Suggested fix

One shared unwrap helper in `BaseOperations` (`LCMObjectWrapper` -> `.lcm_object`, `PythonicWrapper` -> `unwrap()`). Call it from `_GetObject`, `__GetAllomorphObject`, `MorphRuleOperations.__ResolveObject`, start of `ChangeAffixVariant`, item args of base reorder methods, `WfiMorphBundleOperations.__GetMorphObject`/`__GetMSAObject`, `LexSenseOperations.SetGrammaticalInfo`.

The two MorphRule bare-owner bugs (template `Delete`, `__DuplicateAffixTemplate`) occur without wrappers; need `_GetTypedOwner` instead of `_GetObject(Owner.Hvo)`. Track separately.
