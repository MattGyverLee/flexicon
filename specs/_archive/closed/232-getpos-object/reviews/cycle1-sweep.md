# Cycle 1 Sweep — Issue #232 Defect Family (base-typed LCM property reads)

**Scope:** `flexicon/code/**/*.py`. **Method:** grep for `getattr`/`hasattr`/direct reads
against `*RA|RS|RC|OA|OS|OC` names, then trace each variable back to its resolver to see
whether it passed through `cast_to_concrete()` / `cast_phonological_rule()` /
`_GetTypedOwner()` / a `_concrete` wrapper. Property ownership verified via
`flextools_resolve_property` (see Caveats).

## Reference exemplar (excluded from counts)

| file:line | variable | property | class | why |
|---|---|---|---|---|
| `flexicon/code/Lexicon/LexSenseOperations.py:1184` | `msa` | `PartOfSpeechRA` | CONFIRMED BUG | `sense.MorphoSyntaxAnalysisRA` is `IMoMorphSynAnalysis`; prop lives on `IMoStemMsa`/`IMoInflAffMsa`/`IMoUnclassifiedAffixMsa` only — `getattr(...,None)` silently yields `None`. |

## CONFIRMED BUG (16)

| file:line | variable | property read | why |
|---|---|---|---|
| `Lexicon/AllomorphOperations.py:472` | `source` | `PhoneEnvRC` | `__GetAllomorphObject` returns raw `IMoForm`/`ICmObject`, never casts; `PhoneEnvRC` is on `IMoStemAllomorph`/`IMoAffixAllomorph` only. |
| `Lexicon/AllomorphOperations.py:979` | `allomorph` | `PhoneEnvRC` | Same resolver; `GetPhoneEnv` raises `AttributeError` on a raw allomorph or HVO. |
| `Lexicon/AllomorphOperations.py:1025` | `allomorph` | `PhoneEnvRC` | `AddPhoneEnv` — same uncast resolver. |
| `Lexicon/AllomorphOperations.py:1067` | `allomorph` | `PhoneEnvRC` | `RemovePhoneEnv` — same (also line 1068). |
| `Lexicon/LexEntryOperations.py:433` | `allomorph` | `PhoneEnvRC` | Loop var from `source_entry.AlternateFormsOS` is `IMoForm`; deep-Duplicate reads it uncast. |
| `Grammar/PhonologicalRuleOperations.py:918` | `rule` | `RightHandSidesOS` | `__ResolveObject` unwraps wrappers to `_obj` (base `IPhSegmentRule`); `hasattr` is always False → `WireRule` rejects every rule from `GetAll()`/HVO. |
| `Grammar/PhonologicalRuleOperations.py:925` | `rule` | `RightHandSidesOS` | Same variable, direct read. |
| `Grammar/PhonologicalRuleOperations.py:938` | `rule` | `RightHandSidesOS` | Same, inside transaction. |
| `Grammar/PhonologicalRuleOperations.py:942` | `rule` | `RightHandSidesOS` | Same; file has **zero** `cast_to_concrete` uses. |
| `Discourse/ConstChartClauseMarkerOperations.py:290` | `marker` | `WordGroupRA` | Uncast resolver; prop is on `IConstChartMovedTextMarker` only — `GetWordGroup` always returns `None`. |
| `Discourse/ConstChartClauseMarkerOperations.py:327` | `marker` | `DependentClausesRS` | Prop on `IConstChartClauseMarker` only → always returns `[]`. |
| `Discourse/ConstChartClauseMarkerOperations.py:380` | `marker` | `DependentClausesRS` | Same, write path silently skipped. |
| `Discourse/ConstChartWordGroupOperations.py:294` | `group` | `BeginSegmentRA` | Prop on `IConstChartWordGroup`/`ITextTag` only; base is `IConstituentChartCellPart`. |
| `Discourse/ConstChartWordGroupOperations.py:366` | `group` | `EndSegmentRA` | Same. |
| `Grammar/InflectionFeatureOperations.py:1211` | `feature` | `ValuesOC` | `__ResolveFeature` (line 1611) never casts; `ValuesOC` is `IFsClosedFeature`-only → always `[]`. |
| `Notebook/annotation.py:438` | `self._obj` | `BeginObjectRA` | `ICmBaseAnnotation`-only, and unreachable anyway (line 436 `hasattr(_obj,"Owner")` is always True) — dead fallback. |

**Note:** `cast_to_concrete()`'s `_interface_cache` has **no** `ConstChart*`, `IFsClosedFeature`,
or `IPhSegRuleRHS` entries, so the Discourse and feature fixes need cache additions, not just call-site edits.

## NEEDS RUNTIME (19)

| file:line(s) | variable | property | what would settle it |
|---|---|---|---|
| `Grammar/EnvironmentOperations.py:476,532,616,628` | `env` | `LeftContextOA`/`RightContextOA` | Index lists these on `IPhSegRuleRHS` only — i.e. **not on `IPhEnvironment` at all**, which would make these permanently-`None` reads rather than a cast bug. Snapshot has known gaps; check a live `IPhEnvironment` with `dir()`. |
| `Lists/OverlayOperations.py:173,205,420` | `overlay` | `IsVisibleRA`, `ChartRA` | `IsVisibleRA` resolves to nothing in the index; if truly absent, `IsVisible` always returns `True` and `SetVisible` is a silent no-op. Verify against `ICmOverlay`/`ICmPossibility`. |
| `Discourse/ConstChartMovedTextOperations.py:203` | `word_group` | `MovedTextMarkerOA` | Not found in index; confirm the real reverse-reference name on a live chart. |
| `Discourse/ConstChartClauseMarkerOperations.py:128,210,251,442` | `row`/`parent` | `ClauseMarkersOS` | Not found in index (`IConstChartRow` uses `CellsOS`). Confirm live. |
| `Notebook/NoteOperations.py:126,197,345,374,422,602,643` | `note`/`source` | `BeginObjectRA` | `ICmBaseAnnotation`-only, but notes may be minted from `ICmBaseAnnotationFactory` and stay concrete. Check the factory used by `Create`. |

## LIKELY SAFE (9)

`ConstChartWordGroupOperations.py:439` (`ColumnRA` — verified on base `IConstituentChartCellPart`);
`WfiMorphBundleOperations.py:646` (`InterlinearAbbr` on `IMoMorphSynAnalysis`, per issue #110);
`POSOperations.py:847` and `Shared/FilterOperations.py:1139` (both route through `get_pos_from_msa`, which casts);
`LexSenseOperations.py:1397-1402` (`cast_to_concrete` applied at 1397 — the #87 fix);
`MSAOperations.py:517-523,535` (uses `concrete_src`); `Grammar/MorphRuleOperations.py:627,662,808,914`
(`StratumRA` is on both `IMoCompoundRule` and `IMoInflAffixTemplate` bases);
`Grammar/phonological_rule.py`, `Grammar/affix_template.py`, `Grammar/compound_rule.py`,
`Lexicon/allomorph.py` (all read `self._concrete`).

## TECH DEBT (20) — hand-rolled `ClassName` dispatch

`FLExProject.py:3616,4325`; `lcm_casting.py:609,845,849`; `Shared/wrapper_base.py:46,151`;
`Lexicon/LexEntryOperations.py:423-427`; `Lexicon/AllomorphOperations.py:428-443`;
`Lexicon/LexSenseOperations.py:342,1357-1382`; `Lexicon/LexReferenceOperations.py:116,676-680,1216,1278`;
`Lexicon/SemanticDomainOperations.py:704`; `Lists/PublicationOperations.py:879`;
`Lists/PossibilityListOperations.py:1170,1520-1522`; `Notebook/LocationOperations.py:944`;
`Notebook/AnthropologyOperations.py:1735`; `System/CheckOperations.py:1378`;
`System/AnnotationDefOperations.py:1110`; `Grammar/InflectionFeatureOperations.py:1468`.
Not bugs — each picks a factory or owner branch — but they re-implement `cast_to_concrete`'s
ClassName→interface table and drift independently.

## Caveats

Per the standing warning, `liblcm_baseline.json` / the FlexToolsMCP casting index has known
coverage gaps (e.g. it omits `ILexEtymology.Source`, documented as real in CLAUDE.md and
issues #36/#39/#40). Every **CONFIRMED BUG** above is backed by a *positive* index hit showing
the property defined only on concrete subtypes — a claim the gaps cannot manufacture. Every
site whose classification would have depended on an *absence* in the index was demoted to
**NEEDS RUNTIME** instead.

## Totals

| Classification | Count |
|---|---|
| CONFIRMED BUG | 16 (+1 exemplar) |
| NEEDS RUNTIME | 19 |
| LIKELY SAFE | 9 |
| TECH DEBT | 20 |
