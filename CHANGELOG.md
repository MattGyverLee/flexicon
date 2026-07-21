# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Future breaking changes go under `[Unreleased]` until the next version cut.

---

## [Unreleased]

### Fixed
- **`.pyi` stub `GetAll`/`GetAll*` return annotations** across ~40 Operations
  stub files no longer collapse to a blanket `Iterator[Any]`. Each method is
  now annotated with the concrete behavioral-collection shape it actually
  returns per `docs/getall-contract.md`: `EnumerableWrapper[T]`, `list[T]`
  (spelled `List[Any]` for stub compatibility), or a `SmartCollection[T]`
  subtype (`RuleCollection`, `CompoundRuleCollection`,
  `AffixTemplateCollection`, `AllomorphCollection`). `BaseOperations.pyi` now
  declares `EnumerableWrapper` as a proper `Generic[T]` stub class with typed
  `__iter__`/`__len__`/`__getitem__`/`Count`, instead of leaving it
  unshadowed-but-untyped. `BaseOperations.GetAll`'s own declared return type
  changed from `Iterator[Any]` to `Any` -- none of the three real shapes is
  an `Iterator` (no `__next__`), so `Iterator[Any]` at the base would make
  every subclass override an LSP violation under a strict checker.
- **Stale/orphaned `.pyi` paths.** `AllomorphOperations.pyi`,
  `FilterOperations.pyi`, and `MediaOperations.pyi` were shadow-stubbed at
  their pre-refactor locations (`Grammar/`, `TextsWords/`) which no longer
  match the real modules (`Lexicon/`, `Shared/`); a type checker resolving
  those modules got no stub coverage at all. Relocated to match the real
  module paths.
- **Fabricated `GetAll`/`GetAll*` overrides removed or corrected** for
  classes whose stub asserted a per-class `GetAll` override that does not
  exist in the runtime implementation (`InflectionFeatureOperations`,
  `ProjectSettingsOperations`, `PossibilityListOperations`,
  `CheckOperations`, `CustomFieldOperations`, `DiscourseOperations`) --
  these either inherit `GetAll` from a base class or only define a
  `GetAll*`-named sibling method. Also dropped `LexEntryOperations.pyi`'s
  fabricated `GetAllomorphs` stub method, which does not exist in
  `LexEntryOperations.py`.
- **Missing `GetAll*` sibling methods added to stubs** (previously absent
  entirely, so any call site fell through the class's blanket
  `__getattr__ -> Any`): `GetAllCompoundRules`, `GetAllAffixTemplates`,
  `GetAllAffixTemplatesForPOS`, `GetAllAdhocCoProhibitions`,
  `GetAllByMorphType`, `GetAllSenses` (both `LexEntryOperations` and
  `LexSenseOperations`), `GetAllTypes` (`LexReferenceOperations` and
  `VariantOperations`), `GetAllLists`, `GetAllRecordTypes`,
  `GetAllStatuses`, `GetAllCheckTypes`, `GetAllFields`, `GetAllCharts`,
  `GetAllForms`, `GetAllWithStatus`, `GetAllUnapproved`, `GetAllByType`.
  Each now has the real method's parameter signature (positional args and
  defaults) instead of a blanket `*args: Any, **kwargs: Any`, resolving the
  pre-existing signature drift noted as a prerequisite in the original T10
  assessment.

### Deferred (documented, not fixed in this pass)
- Three whole Operations packages (`Discourse/`, `Reversal/`, `Scripture/`)
  have **no `.pyi` stubs at all** -- a pre-existing gap outside this issue's
  scope (adding a new stub tree, not reconciling an existing one).
- The non-`GetAll` methods on every stub (`Find`, `Create`, `Delete`, etc.)
  still use the blanket `*args: Any, **kwargs: Any -> Any`/`__getattr__`
  pattern; only `GetAll`/`GetAll*` methods were reconciled in this pass, per
  the issue's stated scope.

---

## [4.3.0] - 2026-07-20

### Fixed
- **`MediaOperations.GetAll`** now enumerates `ICmFileRepository` directly
  instead of the incorrect `ICmObjectRepository` cast, and its docstring now
  states the caveat that repository enumeration returns every `ICmFile` in
  the database (pronunciation media, external-link files, orphans included),
  which is broader than walking `LangProject.MediaOC`/`PicturesOC` folders.
- **`AgentOperations.GetAll`** now carries the `@OperationsMethod` decorator
  it was missing, matching every other `GetAll` in the codebase.
- **`TranslationTypeOperations.GetSegmentsWithType`** now raises
  `NotImplementedError` instead of silently returning `None`. `ISegment`
  translations have no typed link to a translation-type possibility the way
  text-level translations do, so the method could never do what its name
  promised; it now fails loudly and points callers at `GetTextsWithType()`.

### Changed
- **Build:** the package version is now a single source of truth. `pyproject.toml`
  declares `dynamic = ["version"]` and reads it from the `flexicon.version`
  attribute via `[tool.setuptools.dynamic]`, so the distribution version and the
  runtime `flexicon.version` can no longer diverge (the root cause of the 4.2.0
  stale-version issue). Requires `setuptools>=77` (already pinned in
  `[build-system]`).

### Docs
- **`GetAll`/`GetAll*` collection-return contract**: standardized ~51
  docstrings across ~50 `flexicon/code/**/*Operations.py` files to a
  consistent `Returns:\n    <ContainerType>[<Element>]: ...` form, dropping
  `Yields:` generator-style wording (the `@wrap_enumerable` decorator always
  converts generator bodies to a re-iterable `EnumerableWrapper` before the
  caller sees them, so `Yields:` misdescribed the actual contract).
  `BaseOperations.wrap_enumerable`'s docstring gains a "Behavioral
  collection contract" paragraph explaining the three concrete return
  shapes (`EnumerableWrapper[T]`, `list[T]`, `SmartCollection[T]`
  subtypes) and the loop/`len()`/index/re-iterate guarantee they all
  satisfy. New `docs/getall-contract.md` documents the full guarantee;
  `README.rst` links to it.

---

## [4.2.1]

### Fixed
- **Runtime version string:** bumped the `flexicon.version` attribute in
  `flexicon/__init__.py`, which was left at `4.1.2` during the 4.2.0 cut so
  the published 4.2.0 wheel reported a stale runtime version. Now matches the
  distribution version.

---

## [4.2.0]

### Added
- **`MsaFactoryOperations.CreateStem` / `CreateUnclassifiedAffix`** now
  accept `pos=None` for a category-less stem or unclassified-affix MSA
  (a valid, blank-category-cell FLEx state), mirroring the existing
  `CreateDerivAff` `to_pos=None` precedent. Unblocks cross-project
  transfer of category-less MSAs (9c04ab8).

### Fixed
- **`MsaFactoryOperations.CreateInflAff`** accepts `pos=None` for a
  category-less inflectional affix, matching `CreateStem` /
  `CreateUnclassifiedAffix` (6f316b3).
- **Morph-type classification** unified into a single shared module
  (`Shared/morph_type_utils.py`); `LexEntryOperations`,
  `AllomorphOperations`, and `LexSenseOperations` no longer each carry
  independently drifting stem/affix GUID sets. Fixes a silent logical
  inversion in `LexSenseOperations.__EntryHasAffixMorphType`'s GUID set.
  `MorphRuleOperations.Duplicate` now defaults `deep=True`, matching the
  LexEntry/Text family (#203, #213, #214).
- **`wrap_enumerable`** now catches bare Python iterators/generators (not
  just raw C# `IEnumerable`), so `GetAll()`/`GetAnalyses()`-style methods
  across ~20 Operations classes reliably return a subscriptable,
  `len()`-able collection instead of raising `TypeError` on `entries[0]`
  or `len(entries)` (#201).
- **`MediaOperations.Create`** now owns a new `CmFile` in the appropriate
  `CmFolder` before setting `InternalPath`, fixing a
  `NullReferenceException` that made the add-a-picture/media surface
  (`AddPicture`, `CopyToProject`, `Create`, `AddMediaFile`) unusable.
  `CopyToProject`'s `LinkedFilesRootDir` guard now reads from `ILangProject`
  instead of the `LcmCache` (#226).
- **`GetCustomFieldValue`** on a bare `ITsMultiString` (no
  `BestAnalysisVernacularAlternative` accessor) now resolves the best
  alternative by writing-system priority instead of failing (#224).
  Transaction entry no longer logs a misleading "NoneType is not
  callable" warning when the LCM `Mark` API is unavailable; it logs at
  debug level and proceeds without rollback capability (#221).
- **`BaseOperations._ValidateParam`** guards against stale/deleted LCM
  objects (`IsValidObject is False`), raising `FP_ParameterError` naming
  the parameter instead of an opaque `NullReferenceException` deep
  inside LCM (#205).
- **`SegmentOperations.GetAnalyses`** / `WfiGlossOperations` — polymorphic
  `IAnalysis` tokens (`IWfiWordform` / `IWfiAnalysis` / `IWfiGloss` /
  `IPunctuationForm`) are now resolved by `ClassName` rather than
  `isinstance`, which is unreliable against base-typed LCM refs. Adds
  `SegmentOperations.GetGloss`, `WfiAnalysisOperations.GetCategoryAbbrev`,
  and `GetMorphemeBundles` polymorphic helpers (#212).

### Changed
- **`FLExProject`** singular/plural accessor aliases (e.g.
  `InflectionFeature`/`InflectionFeatures`) are now generated from a
  single table (`_op_aliases.py`, 58 aliases) instead of ~10 hand-written
  properties, closing the gap where a guessed accessor name raised
  `AttributeError`. All previously hand-written aliases are preserved;
  each now emits a `DeprecationWarning` naming the canonical accessor
  (#200).

---

## [4.1.2]

### Fixed
- **Grammar sync:** hardened `Phoneme` synchronization and corrected
  `GetSyncableProperties` in `Phoneme`/`Environment` to distinguish mono
  `ITsString` fields from multi-string fields, preventing type-mismatch errors
  during sync (#222).

### Added
- Syncable-properties support for `PhonFeatures`.

### Changed
- Documentation build pipeline updates: Sphinx configuration, `make.bat`, a
  gh-pages publish workflow on the self-hosted FieldWorks runner, and
  Context7-scoped docs.

---

## [4.1.0]

### Changed
- **Renamed the library from `flexlibs2` to `flexicon`** (distribution name on
  PyPI: `pyflexicon`). flexicon is now maintained as an independent successor
  to cdfarrow/flexlibs rather than a fork; it no longer tracks the upstream
  codebase. Original LGPL-2.1 attribution (Craig Farrow) is retained in
  `LICENSE.txt` / `NOTICE`.
- Packaging consolidated to a single `pyproject.toml` (removed `setup.cfg`);
  corrected the license metadata from `GPL-2.0-or-later` to the actual
  `LGPL-2.1-or-later`.

### Added
- `flexlibs2` compatibility alias: `import flexlibs2` (and deep submodule
  imports such as `flexlibs2.code.lcm_casting`) transparently resolve to the
  identical `flexicon` objects via a meta-path finder, so existing FlexTools /
  FlexTrans scripts keep working. Emits a `DeprecationWarning`.

### Deprecated
- The `flexlibs2` import alias is deprecated and will be **removed in v5.0.0**.
  Update imports to `flexicon`.

---

## [4.0.1] - 2026-06-30

### Fixed

- **`LexEntryOperations.GetComplexFormsNotSubentries`** — none-guard the
  `sense.OwnerOfClass(LexEntryTags.kClassId)` cast. When `OwnerOfClass`
  returns `None` (orphaned sense or test-double context), the unconditional
  `ILexEntry()` cast raised `TypeError`; now returns an empty result,
  mirroring the safer cast pattern already used elsewhere in that file.
  (66b8eb3)

- **`sync/tests/test_base_operations.py`** — corrected a stale import from
  the nonexistent `flexlibs2.flexlibs` module (v1 leftover). The bad import
  raised `ModuleNotFoundError` at collection time and aborted the entire
  pytest session. Corrected to import from the package root `flexlibs2`.
  (742b9b4)

- **`SemanticDomainOperations.GetSubdomains`** — yield `ICmSemanticDomain`
  (typed cast) instead of the base `ICmPossibility` object, for both the
  fast path and the recursive walk.

- **`LocationOperations.GetSublocations`** — yield `ICmLocation` (typed
  cast) for both fast path and recursive walk.

- **`InflectionFeatureOperations.InflectionClassGetAll`** — yield
  `IMoInflClass` (typed cast) instead of the raw base-interface object.
  These three close the Category 5 cast-on-yield gaps. (92762fa)

- **`ProjectSettingsOperations`** — added LCM-backed accessors:
  `GetProjectGuid`, `GetProjectDescription`, `GetExternalLink`,
  `GetAnalysisWritingSystem`, `GetVernacularWritingSystem`. Both WS getters
  return `None` safely when `project.lp` is unavailable. (92762fa, fd156ee)

- **`ReversalIndexEntryOperations.__GetEntryWS`** — raises
  `FP_ParameterError` (naming `entry.Hvo`) when `entry.ReversalIndex` is
  `None`, replacing the `NullReferenceException` that previously surfaced
  during reversal cleanup of orphaned or cascade-deleted entries
  (Category 7). (fd156ee)

### Tests

- **Grammar live tests** (phon-feature, natural-class, phon-rule) refactored
  as self-restoring round-trips. Removed top-of-test pre-clean calls that
  masked incremental failures; each test now follows create -> assert ->
  delete -> assert-gone so a failed test leaves evidence rather than being
  silently swept. 18 tests verified to pass twice back-to-back without a
  DB restore in between. (ddbfe3c)

### Docs

- **`docs/API_ISSUES_CATEGORIZED.md`**: Category 5 marked RESOLVED;
  Category 4 / ProjectSettings table updated to reflect new accessors;
  Category 7 reversal NullReferenceException entry updated with the
  `__GetEntryWS` null-guard fix; additional latent-gap notes added to
  Category 3. (a1d4bb3, 57ed7a0)

---

## [4.0.0] - 2026-06-23

### Changed (Breaking)

- **`flat=` parameter renamed to `recursive=` (inverted semantics) on every hierarchical-list `GetAll()` accessor.** Collection queries default to `recursive=True` (returns every descendant). Passing `flat=` raises `TypeError`. Affected modules:
  - `POSOperations.GetAll`, `LexSenseOperations.GetAll`, `SemanticDomainOperations.GetAll`,
    `AnthropologyOperations.GetAll`, `LocationOperations.GetAll`,
    `PublicationOperations.GetAll`, `PossibilityListOperations.GetAll`,
    plus the inline `GetSubcategories` / `GetSubdomains` / `GetSubitems` helpers.
  - `FLExProject.GetAllSemanticDomains` now also raises `TypeError` on `flat=` (the one-release deprecation shim has been removed).
- **`include_subcategories=` parameter renamed to `recursive=`** on `LexEntryOperations.GetAvailableMorphTypes`. Same semantics, more consistent naming.
- **Counting queries default to `recursive=False`** (FLEx UI parity). `POSOperations.GetEntryCount` was briefly flipped to `recursive=True` in d423e83 and reverted by #101 to match every count column in FLEx's UI (Categories tool, Lexicon Browse, Tools > Statistics — all direct-tag only). `SemanticDomainOperations.GetSenseCount` now accepts the same `recursive=` parameter (default `False`), so caller code looks identical across all `Get*Count` methods. Pass `recursive=True` when you actually want the descendant roll-up.

### Fixed

#### LCM Owner Typing — Pattern A Sweep (2026-05-30)

- **14 raw `Owner` return sites converted to typed casts** across 10 files in
  the Lexicon and TextsWords modules. Untyped `Owner` references silently
  produced wrong parent relationships in `Duplicate` operations and returned
  objects that callers could not navigate without manual casting. All 14 sites
  now cast to the correct interface (e.g. `ILexEntry(obj.Owner)`,
  `ILexSense(obj.Owner)`). (closes #166, closes #168, closes #159)
  - Affected: ExampleOperations, VariantOperations, PronunciationOperations,
    LexReferenceOperations, LexSenseOperations, WfiAnalysisOperations,
    WfiGlossOperations, WfiMorphBundleOperations, SegmentOperations,
    ParagraphOperations

#### API Documentation — Category 8 Correction (2026-05-30)

- **`docs/API_ISSUES_CATEGORIZED.md` Category 8 corrected.** The `Source` field
  row previously listed `ICmBaseAnnotation` as the owner; the field actually
  lives on `IStText`. The stale `ICmBaseAnnotation.Source` is unused dead
  interface; any code relying on it would silently return nothing. Row updated
  to reflect the correct `IStText.Source` owner. (closes #173)
- **`ISegment.BaselineText` entry added** to Category 8. Documents that this is
  an `ITsString` single-WS read-only computed property (backed by
  `IStTxtPara.Contents`) and that writing must go through the
  `Contents`/`ContentsSideEffects`/`AnalysisAdjuster` chain, not direct segment
  assignment.

#### SegmentOperations BaselineText — Partial Fix (2026-05-30, refs #172)

- **`SetBaselineText` write idiom corrected.** Was attempting direct segment
  mutation; now uses `para.Contents.GetBldr().ReplaceTsString(begin, end,
  new_run)` + `para.Contents = bldr.GetString()`, which fires
  `ContentsSideEffects` and lets `AnalysisAdjuster.AdjustAnalysis` maintain
  segment consistency.
- **`GetSyncableProperties` BaselineText read corrected.** Was calling
  `GetMultiStringDict` on an `ITsString` (type mismatch). Now reads the WS
  handle via `bt.get_Properties(0).GetIntPropValues(1, 0)[0]`, verified against
  a live Sena 3 project.
- **Defensive `None` guard** added in `SetBaselineText`; raises
  `FP_ParameterError` on null paragraph.
- **`DeprecationWarning` silenced** in three `SplitSegment`/`MergeSegments`
  internal callers that were passing a deprecated `ws` argument to
  `GetBaselineText`.
- 7 new regression tests (`TestGetSyncablePropertiesBaselineText`) added to
  `tests/test_segment_baseline_text.py`.
- Note: 5 entangled methods (Create, Duplicate, SplitSegment, MergeSegments,
  RebuildSegments) still manually mutate `SegmentsOS`; these require
  architectural rework tracked at #174. **#172 remains open.**

---

## [3.0.0] - 2026-04-07

### Breaking Changes

#### Reversal API Removed (GROUP 6)
- **`project.Reversal` API entirely removed** — 1,343 LOC deleted.
  Migrate to `project.ReversalIndexes` and `project.ReversalEntries`.
  See [docs/REVERSAL_API_MIGRATION.md](docs/REVERSAL_API_MIGRATION.md) for the full per-method table and code examples.
  - `project.Reversal.GetAllIndexes()` → `project.ReversalIndexes.GetAll()`
  - `project.Reversal.GetAll(index)` → `project.ReversalEntries.GetAll(index)`
  - `project.Reversal.GetForm(entry)` → `project.ReversalEntries.GetForm(entry)`
  - `project.Reversal.SetForm(entry, text)` → `project.ReversalEntries.SetForm(entry, text)`
  - `project.Reversal.Create(index, form, ws)` → `project.ReversalEntries.Create(index, form, ws)`

#### Lists Consolidation (GROUP 8)
- **`AgentOperations`, `PublicationOperations`, `TranslationTypeOperations`, and `OverlayOperations`
  now inherit from `PossibilityItemOperations`** instead of duplicating CRUD methods.
  Most caller code is unchanged; see [docs/RELEASE_v3_0_0.md](docs/RELEASE_v3_0_0.md) for full details.
  Known follow-up issues: `AgentOperations` (#54) and `OverlayOperations` (#149) have partial
  parent-class fit problems; some inherited methods may not function correctly.

### Changed
- Net -3,686 LOC since v2.4.0 (6,583 deletions, 2,897 additions) from deprecated-code removal.

---

## [2.4.0] - 2026-03-22

### Added

#### Transaction & Undo/Redo Framework (MAJOR)
- **Safe Transaction Rollback** - Phase 1 implementation for safe undo/redo operations
  - Automatic transaction state tracking
  - Rollback recovery for failed operations
  - Integration with FieldWorks LCM transactions
  - Comprehensive testing guide in docs/TESTING_UNDO_REDO.md

#### Security Enhancements
- **Write-Enable Guards** - 7 untagged mutating methods now protected
  - Prevents accidental modifications in read-only mode
  - `_EnsureWriteEnabled()` guards on all mutation points
  - Protects data integrity across all Operations classes

#### Pre-commit Hooks & Quality Control
- Custom decorator validator prevents duplicate decorators
- Black code formatting enforcement
- Flake8 linting (unused imports, complexity)
- Detect-secrets for credential detection
- Setup documentation in docs/PRE_COMMIT_SETUP.md
- Decorator checking script in scripts/check_decorators.py

### Fixed

#### Decorator Bugs
- **Duplicate `@OperationsMethod` decorators** - Fixed `'OperationsMethod' object is not callable'` errors
  - BaseOperations.py: Removed duplicates from 9 reordering/sync methods
  - POSOperations.py: Removed duplicates from 17 methods (including GetAll)
  - LexEntryOperations.py: Removed duplicates from 5 methods
  - All 64 operation files verified clean

### Documentation

#### New Guides
- **TESTING_UNDO_REDO.md** - Comprehensive undo/redo testing strategy and examples
- **TRANSACTION_GUIDE.md** - Transaction management and error recovery patterns
- **CONTRACT_TESTING.md** - LibLCM contract testing for API compatibility

### Tested Against

- LibLCM Contract Test Suite - Validates API compatibility across versions
- Unit tests for undo/redo implementation
- Pre-commit hooks prevent regression

### Breaking Changes

None. Fully backward compatible with v2.3.x APIs.

---

## [2.3.0] - 2026-02-28

### Added

#### Extended Wrapper Classes
- **Allomorph**: Wrapper for allomorph variants and forms
  - Form and gloss access with normalization
  - Environment context tracking
  - Variant relationship management

- **CompoundRule**: Wrapper for compound rule definitions
  - Rule component access
  - Directional compound rules
  - Integration with morpheme inventories

- **AdhocProhibition**: Wrapper for morphosyntactic prohibitions
  - Prohibited morpheme combinations
  - Context-aware blocking rules
  - Exception handling

- **Annotation**: Wrapper for project annotations and notes
  - Annotation type identification
  - Content and metadata access
  - Author and timestamp tracking

- **AffixTemplate**: Wrapper for morpheme slot templates
  - Slot configuration and ordering
  - Prefix and suffix slot management
  - Obligatory/optional slot constraints

#### Smart Collections (Extended)
- **AllomorphCollection**: Type-aware collection for allomorphs
- **CompoundRuleCollection**: Unified collection for compound rules
- **ProhibitionCollection**: Collection for morphosyntactic prohibitions
- **AnnotationCollection**: Collection for project annotations
- **AffixTemplateCollection**: Collection for affix templates

#### Type Hints and IDE Support
- Python type hints on all wrapper class properties (18+ properties)
- Improved IDE autocomplete and type checking
- Better static analysis support

#### Documentation
- **USAGE_ALLOMORPHS.md**: Allomorph operations guide
- **USAGE_COMPOUND_RULES.md**: Compound rule operations guide
- **USAGE_PROHIBITIONS.md**: Morphosyntactic prohibition guide
- **USAGE_ANNOTATIONS.md**: Annotation operations guide
- **USAGE_AFFIX_TEMPLATES.md**: Affix template operations guide

### Improved

- **Code Quality**: Type hints across all wrapper classes
- **Documentation**: Usage guides for all new domains
- **Test Coverage**: Extended test suite for new wrappers
- **API Consistency**: All collections follow unified interface

### Backward Compatibility

- **100% Maintained**: All v2.0 and v2.1 APIs unchanged
- **Additive Only**: New wrappers don't modify existing functionality
- **Mixed Usage**: Old and new approaches coexist seamlessly

### Deprecation Notices

None. All previous APIs remain fully functional.

---

## [2.2.0] - 2025-02-28

### Added

#### Wrapper Classes
- **PhonologicalRule**: Unified wrapper for PhRegularRule, PhMetathesisRule, and PhReduplicationRule
  - Transparent casting to concrete types
  - Capability-based API (`has_output_specs`, `has_metathesis_parts`, `has_reduplication_parts`)
  - Convenience properties for common operations
  - Full backward compatibility with base interface

- **MorphosyntaxAnalysis**: Unified wrapper for MoStemMsa, MoDerivAffMsa, MoInflAffMsa, and MoUnclassifiedAffMsa
  - Type identification properties (`is_stem_msa`, `is_deriv_aff`, `is_infl_aff`)
  - Automatic casting based on actual type
  - Convenience properties for POS access
  - Proper string representation showing actual type

- **PhonologicalContext**: Unified wrapper for PhSimpleContextSeg, PhSimpleContextNC, PhComplexContext, and PhBoundaryContext
  - Context type detection (`is_simple_context`, `is_complex_context`, `is_boundary_context`)
  - Segment-based vs natural class detection
  - Convenience properties for accessing context-specific data
  - Clear display of context type

#### Smart Collections
- **RuleCollection**: Collection class for phonological rules
  - Type-aware display showing breakdown of rule types
  - Convenience filter methods (`regular_rules`, `metathesis_rules`, `reduplication_rules`)
  - Custom filtering with `filter_where()` across all rule types
  - Support for method chaining

- **MSACollection**: Collection class for morphosyntactic analyses
  - Type-aware display showing MSA type breakdown
  - Convenience filters (`stem_msas`, `deriv_aff_msas`, `infl_aff_msas`, `unclassified_aff_msas`)
  - POS-based filtering (`filter_by_pos()`)
  - Advanced filtering with `filter_by_has_pos()`, `filter_where()`

- **ContextCollection**: Collection class for phonological contexts
  - Type-aware display with context type breakdown
  - Convenience filters for all context types
  - Custom filtering capabilities
  - Full iteration and indexing support

#### Base Infrastructure
- **LCMObjectWrapper**: Base class for all wrapper implementations
  - Automatic delegation to concrete interfaces
  - Consistent property access across types
  - Exception handling for missing properties
  - `__getattr__` delegation pattern for seamless access

- **SmartCollection**: Base class for all collection types
  - Type-aware string representation
  - By-type filtering with `by_type()`
  - Generic filtering framework
  - Standard collection operations (append, extend, clear)

### Improved

- **Type Transparency**: Users no longer need to manually check `ClassName` and cast to concrete types
- **IDE Support**: Wrapper classes provide better autocomplete and type hints
- **Error Messages**: Type mismatches produce clear, actionable error messages
- **Filtering**: Unified filtering across type hierarchies without manual type checking
- **Documentation**: Comprehensive examples in docstrings and test suite
- **Code Maintainability**: Internal casting hidden from public API, reducing complexity

### Fixed

- **AttributeError Prevention**: Capability checks prevent accessing unavailable properties
- **Type Safety**: Automatic casting ensures correct interface access
- **Method Chaining**: Collections support fluent filtering patterns

### Documentation

- **MIGRATION.md**: Complete migration guide showing old vs new API
  - Side-by-side examples for all three domains
  - Backward compatibility notes
  - Gradual vs immediate migration strategies
  - Feature comparison table

- **Wrapper Classes Documentation**: Comprehensive docstrings
  - Usage examples in all wrapper classes
  - Capability-based API documented
  - Type detection methods explained

- **Smart Collections Guide**: Collection usage patterns
  - Filtering examples
  - Type-aware display explanation
  - Convenience method documentation

### Backward Compatibility

- **Zero Breaking Changes**: All existing v2.1 code runs unchanged
- **Additive Design**: New wrappers are purely additive, don't modify existing API
- **Mixed Usage**: Old and new approaches can coexist in same codebase
- **Gradual Migration**: Users can migrate at their own pace
- **Base Interface Access**: Direct access to base ILcmObjects still available

### Tests

**Core Wrapper Tests** (41 tests)
- LCM Object wrapper initialization and delegation
- Concrete property access across types
- Exception handling and edge cases
- Attribute error prevention

**Collection Tests** (70 tests)
- SmartCollection initialization and operations
- Indexing, slicing, iteration
- Type-aware string representation
- By-type filtering and custom filtering

**Domain-Specific Tests** (68 tests)
- **Phonological Rules**: RuleCollection and PhonologicalRule wrapper
  - Regular rule properties
  - Metathesis rule properties
  - Reduplication rule properties
  - Convenience filters and chaining

- **MSAs**: MSACollection and MorphosyntaxAnalysis wrapper
  - Stem MSA properties and filters
  - Derivational affixal MSA properties
  - Inflectional affixal MSA properties
  - POS-based filtering and detection

- **Contexts**: ContextCollection and PhonologicalContext wrapper
  - Simple context (segment-based) properties
  - Simple context (natural class) properties
  - Complex context properties
  - Boundary context properties
  - Type convenience filters

**Total: 179 tests passing, 0 failures, 0 regressions**

### Performance

- No performance degradation compared to v2.1
- Wrapper overhead minimal (delegation pattern)
- Collection operations O(n) as expected
- Lazy evaluation in filter chains

### Known Limitations

- Wrappers currently available for three domains:
  - Grammar: Phonological Rules
  - Lexicon: Morphosyntactic Analyses
  - Grammar: Phonological Contexts
- Other domains will receive wrapper support in v2.3+
- Direct operations still available for all domains

### Deprecation Notices

None. All v2.1 API remains fully functional.

---

## [2.1.0] - Previous Release

See git history for previous changelog entries.

---

## How to Upgrade

### From Earlier Versions to v2.3.0

No action required. Simply upgrade the package:

```bash
pip install flexlibs2==2.3.0
```

Existing code will continue to work unchanged. All v2.0, v2.1, and v2.2 APIs remain fully functional.

### Using Wrapper Classes

To use the latest wrappers for additional domains:

```python
from flexlibs2.wrappers import Allomorph, CompoundRule, AffixTemplate
from flexlibs2.collections import AllomorphCollection, CompoundRuleCollection

# Work with allomorphs transparently
allomorphs = project.Allomorph.GetAll()
for allomorph in allomorphs:
    print(f"{allomorph.form}: {allomorph.gloss}")
```

Existing code continues to work without modification.

---

## Future Roadmap

### v2.4.0 (Planned)

- Performance optimizations for large collections
- Advanced query builder pattern
- Integration with FLEx import/export
- Extended wrapper support for remaining domains

### v3.0.0 (Future)

- Complete wrapper coverage for all domains
- Potential breaking changes for major improvements
- Enhanced type safety with static typing

---

## Contributing

See CONTRIBUTING.md for guidelines on contributing to FlexLibs2.

---

## Version Support

- **v2.3.x**: Current stable release, actively maintained
- **v2.2.x**: Previous stable, maintenance only
- **v2.1.x**: Legacy, security fixes only
- **v2.0.x**: End of life
- **v1.x**: End of life

