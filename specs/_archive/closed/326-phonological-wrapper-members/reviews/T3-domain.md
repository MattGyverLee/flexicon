# T3 Domain Ruling — Issue #326

## Decisions

| decision | rationale | FLEx-user mapping |
|---|---|---|
| `segment` and `natural_class` return `FeatureStructureRA`, typed/cast as `IPhPhoneme` and `IPhNaturalClass` respectively. | T1 reflection shows these are the actual links; `SegmentRA` and `NaturalClassRA` are not LCM members. The property name is historical and does not mean the value is an `IFsFeatStruc`. | In a phonological environment, a simple segment context points to a phoneme, while a simple natural-class context points to a natural class. |
| Keep `has_metathesis_parts` and `metathesis_parts`; derive the two parts from `StrucDescOS` slices using `LeftSwitchIndex`/`LeftSwitchLimit` and `RightSwitchIndex`/`RightSwitchLimit`. | The live API has no part collections. The switch ranges are the same structural information the FLEx rule editor presents as the two swapped portions; exposing raw indices as the primary API would leak LCM implementation details. Invalid/unset ranges should produce empty parts. | Users see “left swapped part” and “right swapped part” as context sequences, matching how they describe and edit a metathesis rule. | 
| Remove reduplication properties, `reduplication_rules()`/`redup_rules()`, and all `PhReduplicationRule` documentation. Do not deprecate. | Live reflection found no reduplication class, interface, factory, or instances across 89 projects; retaining these claims creates a capability that cannot exist in the supported LCM. Public-API transition concerns remain for lex-author. | FLEx users can work with the two live phonological rule kinds: regular and metathesis; no fictional reduplication rule is advertised. |

### Domain conclusion

The wrapper should model the live FLEx/LCM object model and preserve user-facing concepts rather than invented CLR member names. The context links are phoneme/natural-class objects, metathesis parts are structural-description slices, and reduplication is not a supported FLEx rule concept in this LCM.
