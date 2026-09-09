# Issue #276 -- code survey (static, no live LCM required)

Read-only survey of what each "grammatical category" reading is already
served by. No code changed. Gathered 2026-09-09.

## 1. What GramCatOperations actually reads

`flexicon/code/Grammar/GramCatOperations.py:115-125` -- `GetAll` walks
`lp.MsFeatureSystemOA.TypesOC`. Elements are `IFsFeatStrucType`, which
per the checked-in LibLCM 11.0.0 baseline is not an `ICmPossibility` and
has no `SubPossibilitiesOS`.

Downstream consequences in the same file:

| Site | Line | Effect |
|------|------|--------|
| `GetAll(recursive=True)` | 122 | `hasattr` guard correctly False; recursion unreachable, silent |
| `Create(name, parent=...)` | 195-198 | `parent_obj.SubPossibilitiesOS` -- property absent on the type |
| `GetSubcategories` | 375-383 | same, returns empty for every element GetAll yields |
| `GetParent` | 436-445 | `ICmPossibility(cat.Owner)` -- owner is the feature system |
| `Delete` | 250 | `TypesOC.Remove(cat)` unconditional; a subcategory would no-op |
| `Duplicate` | 529-535 | top-level branch appends a fresh `IFsFeatStrucType` |

## 2. Both candidate readings are ALREADY owned elsewhere

### List level -- POS
`flexicon/code/Grammar/POSOperations.py` owns
`lp.PartsOfSpeechOA.PossibilitiesOS` (note: the possibilities of the
list, not the list object). Casts elements to `IPartOfSpeech`. Full
surface: `GetAll(recursive=)`, `Create(name, abbreviation,
catalogSourceId=)`, `Delete`, `Exists`, `Find`, `GetName`/`SetName`,
`GetAbbreviation`/`SetAbbreviation`, `GetSubcategories(recursive=)`,
`AddSubcategory`, `RemoveSubcategory`, `GetCatalogSourceId`,
`GetInflectionClasses`, `GetAffixSlots`, `GetEntryCount`, `Duplicate`,
plus `CatalogBackedMixin` (GOLD import).

### Feature-struc-type level -- InflectionFeatures
`flexicon/code/Grammar/InflectionFeatureOperations.py` already owns
`MsFeatureSystemOA.TypesOC` properly, with correct `IFsFeatStrucType`
semantics: `TypeFind` (:582) and `TypeCreate` (:621). The collection
GramCat reads today therefore has a legitimate owner that is not
GramCat.

### Entry/sense level -- the MSA composite
`flexicon/code/Lexicon/LexSenseOperations.py` already implements the
list-vs-entry split the owner hypothesised:

| Method | Line | Returns |
|--------|------|---------|
| `GetGrammaticalInfo(sense)` | 1526 | `sense.MorphoSyntaxAnalysisRA` -- the MSA itself |
| `SetGrammaticalInfo(sense, msa)` | 1561 | assigns the MSA |
| `GetPartOfSpeech(sense)` | 1132 | `MorphoSyntaxAnalysisRA.InterlinearAbbr` (rendered string) |
| `GetPartOfSpeechObject(sense)` | 1177 | the `IPartOfSpeech` behind the MSA |
| `SetPartOfSpeech(sense, pos, msa_kind=)` | 1245 | creates/retargets the MSA |

`flexicon/code/Lexicon/MSAOperations.py` covers MSA construction
(`CreateStem`, `CreateDerivAff`, `CreateInflAff`,
`CreateUnclassifiedAffix`, `SetStemMsaPos`, `SetDerivAffMsaPos`), and
`morphosyntax_analysis.py` wraps it with `pos_main` / `pos_from` /
`pos_to` and `is_*_msa` capability checks.

**So GramCat serves neither reading.** It is a vestigial third surface
over a collection that belongs to InflectionFeatures.

## 3. The codebase has already converged on the other spellings

Newer code documents `project.POS.Find("Verb")`:
- `LexSenseOperations.py:1177` `GetPartOfSpeechObject` docstring.

Older code documents `project.GramCat.Find("Verb")`:
- `FLExProject.py:1876` (the `MSA` property docstring)
- `Lexicon/MSAOperations.py:141-146` (class docstring)

Both of those are broken twice over:
1. `GramCatOperations` defines no `Find` and no `Exists` at all -- the
   call raises `AttributeError`. `GramCatOperations.pyi` declares both
   anyway, so the stub advertises a surface that does not exist.
2. Even with a `Find`, "Verb" is not in `TypesOC`.

Their intent is unambiguous though: they wanted a POS to hand to
`project.MSA.CreateStem(sense, verb_pos)`. That is list-level POS.

## 4. Blast radius

Public surface:
- `flexicon/__init__.py:147` exports `GramCatOperations`.
- `FLExProject.py:1712-1734` exposes `project.GramCat`.
- `_op_aliases.py:83` maps deprecated `GramCats` -> `GramCat`.
- Precedent for a delegating alias: `FLExProject.py:1681` `Features`
  -> `InflectionFeatures`, with a docstring explaining the FLEx-UI
  spelling it serves.

Signature clash if GramCat becomes POS-backed:
- `GramCat.Create(name, parent=None)` -- no abbreviation, hierarchical
- `POS.Create(name, abbreviation, catalogSourceId=None)` -- abbreviation
  mandatory and positional; children go via `AddSubcategory(pos, name,
  abbreviation)`

`project.GramCat.Create("Transitive")` appears in `FLExProject.py:1728`
and in `examples/grammar_gramcat_operations_demo.py:89`.

Tests:
| File | Coupling | Fate |
|------|----------|------|
| `tests/operations/test_collection_cast_pattern.py:836` `TestGramCatGetAllRecursionClaim` | asserts `"MsFeatureSystemOA" in` GetAll source | must be updated -- it fails BY DESIGN when GetAll is repointed |
| same file :712-714 | parametrized row for `GetSubcategories`/`SubPossibilitiesOS` | revisit |
| `tests/operations/test_gramcat_duplicate.py` | mock-only; reimplements the TypesOC path in `_simulate_*` helpers, never imports the real class | obsolete under a POS-backed GramCat |
| `tests/phase2_validation_tests.py:664` `TestGramCatOperations` | only exercises `_EnsureWriteEnabled` / `_ValidateParam` | survives unchanged |
| `tests/test_operations_baseline.py:79` | imports the class by name | survives iff the class name persists |
| `tests/contract/snapshots/expected_contract.json` | records per-file imports, incl. `IFsFeatStrucTypeFactory`, `ICmPossibilityFactory` for this file | regenerate |
| `tests/conftest.py:162,743` | module registration | survives iff name persists |

Docs: `docs/API_ISSUES_CATEGORIZED.md:693` (row "Site 4", TypesOC
Duplicate, marked DONE for #158) becomes moot;
`docs/MIGRATION_GUIDE.md` and `CHANGELOG.md` need entries.

## 5. Data hazard

`GramCat.Create(name)` today creates a real `IFsFeatStrucType` via
`IFsFeatStrucTypeFactory` and adds it to `MsFeatureSystemOA.TypesOC`
(line 200-203). Any caller who used it has written stray
feature-struc-types into their project's feature system. These are
indistinguishable from types legitimately created by
`InflectionFeatures.TypeCreate`, so automated cleanup cannot be
targeted safely -- see the ruling for whether that matters.
