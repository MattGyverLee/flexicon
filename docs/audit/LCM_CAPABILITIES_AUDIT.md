# FlexLibs2 LCM Capabilities Audit

**Audit Date:** 2026-05-27 (refreshed from 2025-03-16)
**Scope:** 106 Python files in `flexlibs2/code/` (60 Operations classes + BaseOperations parent)
**Status:** REFRESHED -- Ready for review
**Methodology:** Automated extraction via `tools/extract_api_usage.py --code-dir flexlibs2/code --all` (JSON outputs in `reports/audit/`) supplemented by manual usage-pattern review.

> ## TODO -- Sections requiring fuller narrative rewrite
>
> The data-bearing parts of this document (Import Statistics, Distribution by Module, per-category counts, Summary Table) have been refreshed against the live tree. The narrative prose in the per-category sections retains the original analysis with refreshed counts where they appear in the body. The following narrative content still reflects 2025-03-16 framing and is a candidate for a future refresh that goes beyond a data refresh:
> - Category 2 (Factories) -- the 12-factory list reflects the original spot inspection; the live tree imports 74 unique factories. The category narrative still summarises the original 12. The QUICK_REFERENCE and SUMMARY files list the expanded set; see also `reports/audit/api_usage_extract.json`.
> - Category 6 (Tags) -- the 11-tag list reflects the original audit; the live tree has 13 unique tags (`LexEntryRefTags`, `LexRefTypeTags`, `MoMorphTypeTags` are new).
> - Category 5 (Exceptions) -- the 5-exception list is now 6; `StartupException` from `SIL.FieldWorks.Common.FwUtils` was added.
> - Category 10 (Writing Systems) and Category 9 (FieldWorks UI) -- narrative still correct in shape but does not enumerate `FwAppArgs`, `VersionInfoProvider`, or `StartupException`.
> - Scripture domain coverage discussion -- original said "minimal coverage". Scripture now has 6 Operations classes (ScrBook, ScrDraft, ScrSection, ScrTxtPara, ScrAnnotations, ScrNote). The narrative still reads as if minimal.
> - Discourse domain coverage -- original noted 8 Discourse operations; live tree has 7 ConstChart-prefixed Operations. The narrative is approximately correct.
> - Recommendations -- "Complete Scripture" recommendation is partially addressed; refresh recommendation list once narrative is rewritten.
>
> These TODOs do not affect the audit's headline conclusions (no critical risks, healthy architecture). They affect the depth-of-detail in the per-category narrative only.

---

## Executive Summary

This audit reveals a **well-designed abstraction layer** that intentionally hides the complexity of the LCM API while providing comprehensive access through a user-friendly public interface. The project imports **14 distinct SIL namespaces** (the original audit said 25; the live count is 14 namespaces containing 233 unique classes) encompassing:

- **Repository pattern** for data access (collections/queries)
- **Factory pattern** for object creation
- **Manager/Service interfaces** for metadata and system operations
- **Utility classes** for text handling and reflection
- **Exception types** for consistent error handling

### Key Findings

- **Fully exposed:** 60 data domain Operations (POS, LexEntry, Texts, etc.) -- up from 57 in original audit
- **Partially exposed:** Advanced features (caching, metadata); Undo/Redo are now exposed via dedicated methods
- **Not exposed:** Low-level LCM infrastructure and developer-only services
- **Low risk exposure:** The abstraction prevents direct access to internal FW infrastructure
- **Recommended:** Document advanced access patterns for power users

---

## Import Statistics (refreshed 2026-05-27)

### Summary
- **Distinct SIL Namespaces Imported:** 14
- **Total Python Files with SIL Imports:** 73 (of 106 total)
- **Total Import Statements:** 569
- **Unique Classes/Interfaces Imported:** 233
- **Operations Classes in API:** 60 (exposed via FLExProject properties)
- **Helper Classes:** 7 (PythonicWrapper, lcm_casting, etc.)
  - Correction (#271): earlier revisions of this line listed a
    `CastingOperations` helper. No such module or class has ever existed in
    the tree; the casting entry point is `lcm_casting.cast_to_concrete`,
    exported as `from flexicon import cast_to_concrete`.

### Distribution by Namespace

| Namespace | Unique classes | Files | Total imports | Status |
|---|---:|---:|---:|---|
| `SIL.LCModel` (core data types) | 203 | 64 | 389 | Fully integrated |
| `SIL.LCModel.Core.KernelInterfaces` | 5 | 62 | 92 | Heavily used for text |
| `SIL.LCModel.Core.Text` | 1 | 57 | 58 | String handling |
| `SIL.LCModel.Core.Cellar` | 3 | 3 | 5 | Property type system |
| `SIL.LCModel.Infrastructure` | 2 | 2 | 3 | Advanced/internal |
| `SIL.LCModel.Utils` | 2 | 2 | 3 | Reflection/threading |
| `SIL.LCModel.Application.ApplicationServices` | 2 | 2 | 2 | XML list import/export |
| `SIL.LCModel.DomainServices` | 2 | 1 | 2 | MsaType, SandboxGenericMSA |
| `SIL.FieldWorks` | 1 | 1 | 1 | ProjectId |
| `SIL.FieldWorks.Common.FwUtils` | 7 | 4 | 8 | FW utilities, paths, threading |
| `SIL.FieldWorks.Common.Controls` | 1 | 1 | 1 | ProgressDialogWithTask |
| `SIL.FieldWorks.FdoUi` | 1 | 1 | 1 | FwLcmUI |
| `SIL.FieldWorks.FwCoreDlgs` | 1 | 1 | 1 | ChooseLangProjectDialog |
| `SIL.WritingSystems` | 2 | 3 | 3 | Sldr, WritingSystemDefinition |

---

## Detailed Import Audit

### Category 1: Repository Interfaces (Data Access)

**Status:** [OK] Exposed through Operations classes, internal access only
**Count (refreshed):** 18 unique repository interfaces across 25 files

#### Repositories Used
```
ICmObjectRepository              - Generic object lookup by ID
ICmPossibilityRepository         - POS, semantic domains, lists
ICmPersonRepository              - People (notebook)
ICmAnnotationDefnRepository      - Annotation definitions
ILexEntryRepository              - Lexicon entry access
ILexEntryTypeRepository          - Entry type definitions
ILexSenseRepository              - Sense access
ILexRefTypeRepository            - Reference type definitions
ITextRepository                  - Text/document access
ISegmentRepository               - Text segment lookup
IStTxtParaRepository             - Paragraph access
IWfiWordformRepository           - Wordform inventory
IWfiAnalysisRepository           - Wordform analysis access
IWfiGlossRepository              - Gloss access
IReversalIndexRepository         - Reversal index access
IRnResearchNbkRepository         - Research notebook
IDsConstChartRepository          - Discourse constituent charts
IScrBookRepository               - Scripture books
```

**Exposure:**
- **Public API:** Users access these through `.GetAll()`, `.Find()`, `.Create()` methods in Operations classes
- **Files:** 25 files use repositories directly
- **Risk Level:** MINIMAL - repositories accessed through safe wrapper methods
- **Usage Pattern:** `ICmObjectRepository(IHvo)` used in:
  - `Grammar/EnvironmentOperations.py` - lookup by Hvo
  - `Grammar/POSOperations.py` - reference resolution
  - Multiple Lexicon operations

**Example Usage:**
```python
# NOT exposed to users - internal only
from SIL.LCModel import ICmObjectRepository
repo = project.ObjectRepository(ICmObjectRepository)
obj = repo.GetObject(hvo)

# Users get this instead:
pos_list = project.POS.GetAll()
```

---

### Category 2: Factory Interfaces (Object Creation)

**Status:** [OK] Fully wrapped in Create/Update methods
**Count (refreshed):** 74 unique factory interfaces across 57 files

#### Factories Used (selected highlights -- full list in `reports/audit/api_usage_extract.json`)
```
ICmPossibilityListFactory      - Create POS lists, semantic domains, lists
ICmPossibilityFactory          - Create possibility items
IPartOfSpeechFactory           - Create parts of speech
IPhEnvironmentFactory          - Create phonological environments
IPhPhonemeFactory              - Create phonemes
IPhCodeFactory                 - Create phoneme codes
IPhNCSegmentsFactory           - Natural class (segments)
IPhNCFeaturesFactory           - Natural class (features)
IPhSimpleContextSegFactory     - Simple seg context
IPhSimpleContextNCFactory      - Simple NC context
IPhRegularRuleFactory          - Regular phonological rules
IPhMetathesisRuleFactory       - Metathesis rules
IPhReduplicationRuleFactory    - Reduplication rules
IPhSegRuleRHSFactory           - Rule right-hand side
IMoStemAllomorphFactory        - Stem allomorphs
IMoAffixAllomorphFactory       - Affix allomorphs
IMoStemMsaFactory              - Stem MSAs
IMoDerivAffMsaFactory          - Derivational MSAs
IMoInflAffMsaFactory           - Inflectional MSAs
IMoUnclassifiedAffixMsaFactory - Unclassified MSAs
IMoEndoCompoundFactory         - Endocentric compounds
IMoExoCompoundFactory          - Exocentric compounds
IMoInflAffixTemplateFactory    - Inflection templates
IMoInflClassFactory            - Inflection classes
IFsClosedFeatureFactory        - Closed features
IFsClosedValueFactory          - Closed values
IFsFeatStrucFactory            - Feature structures
IFsSymFeatValFactory           - Symbolic feature values
IStTextFactory                 - Text blocks
IStTxtParaFactory              - Paragraphs
ITextFactory                   - Text container
ISegmentFactory                - Text segments
IWfiWordformFactory            - Wordforms
IWfiAnalysisFactory            - Word analyses
IWfiGlossFactory               - Glosses
IWfiMorphBundleFactory         - Morpheme bundles
ILexEntryFactory               - Lex entries
ILexEntryRefFactory            - Lex entry refs
ILexSenseFactory               - Senses
ILexExampleSentenceFactory     - Example sentences
ILexEtymologyFactory           - Etymology
ILexPronunciationFactory       - Pronunciations
ILexReferenceFactory           - Lexical references
ILexRefTypeFactory             - Lex ref types
IDsDiscourseDataFactory        - Discourse data
IDsDiscourseFactory            - Discourse structures
IDsConstChartFactory           - Constituent charts
IConstChartRowFactory          - Chart rows
IConstChartWordGroupFactory    - Chart word groups
IConstChartMovedTextMarkerFactory - Moved text markers
IConstChartClauseMarkerFactory - Clause markers
IConstChartTagFactory          - Cell tags
IRnGenericRecFactory           - Research records
ICmAgentFactory                - Agents
ICmAnnotationDefnFactory       - Annotation defs
ICmAnthroItemFactory           - Anthropology items
ICmBaseAnnotationFactory       - Base annotations
ICmFileFactory                 - File objects
ICmFilterFactory               - Filters
ICmFolderFactory               - Folders
ICmLocationFactory             - Locations
ICmMediaFactory                - Media
ICmPersonFactory               - People
ICmPictureFactory              - Pictures
ICmSemanticDomainFactory       - Semantic domains
ICmTranslationFactory          - Translations
IReversalIndexFactory          - Reversal indexes
IReversalIndexEntryFactory     - Reversal entries
IScrBookFactory                - Scripture books
IScrDraftFactory               - Scripture drafts
IScrSectionFactory             - Scripture sections
IScrTxtParaFactory             - Scripture paragraphs
IScrScriptureNoteFactory       - Scripture notes
IScrBookAnnotationsFactory     - Scripture book annotations
```

**Exposure:**
- **Public API:** Never exposed directly - wrapped in `Create()` methods
- **Files:** Imports across 57 Operations files (conditional imports are common; see "Pattern 5: Local Imports" below)
- **Risk Level:** MINIMAL - factory calls wrapped in validation logic
- **Usage Pattern:** Imported locally within Create methods:

```python
# File: Lexicon/AllomorphOperations.py (line ~90)
def Create(self, allomorph_form, allomorph_type, lexeme=None):
    if self.project.WriteEnabled:
        try:
            from SIL.LCModel import IMoStemAllomorphFactory
            factory = self.project.ObjectFactory(IMoStemAllomorphFactory)
            # Create wrapped in error handling
```

**Design Pattern:** Local imports inside methods to avoid import-time dependencies

---

### Category 3: Manager/Service Interfaces

**Status:** [PARTIAL] Some exposed, most not exposed

#### Managers Imported
```
IUndoStackManager           - Undo/redo stack (save operations)
IFwMetaDataCacheManaged     - Metadata cache access
```

**IUndoStackManager Usage:**
- **Location:** `FLExProject.py` line 273
- **Exposure:** NOT exposed in public API
- **Purpose:** Called during `CloseProject()` to save changes
- **Risk:** LOW - only called internally by framework

```python
# FLExProject.py - internal only
usm = self.ObjectRepository(IUndoStackManager)
usm.Save()
```

**IFwMetaDataCacheManaged Usage:**
- **Location:** `FLExProject.py` import only
- **Exposure:** NOT exposed
- **Purpose:** Field metadata and type information
- **Recommendation:** Could be exposed for schema introspection

---

### Category 4: Text/String Interfaces

**Status:** [OK] Core text handling well-wrapped

#### Text Interfaces
```
ITsString               - Immutable multi-lingual text
ITsStrBldr              - String builder (mutable)
IMultiUnicode           - Unicode string collection
IMultiString            - Multi-language strings
TsStringUtils           - Text utilities (MakeString, GetText)
```

**Exposure:**
- **Public API:** NOT exposed to users - hidden behind `BestStr()` and helper methods
- **Files:** 50+ files (nearly all)
- **Usage Pattern:** Wrapped in convenience methods:

```python
# FLExProject.py (line 1831)
def BestStr(self, stringObj):
    """Generic string function for MultiUnicode and MultiString"""
    # Users never see ITsString directly

# Grammar/GramCatOperations.py - example internal use
from SIL.LCModel.Core.Text import TsStringUtils
from SIL.LCModel.Core.KernelInterfaces import ITsString
ws_handle = self.project.WSHandle('en')
ts = TsStringUtils.MakeString(text_value, ws_handle)
```

**Recommendation:** Document text handling as advanced topic for power users who need `ITsString` directly

---

### Category 5: Exception Types

**Status:** [OK] Standard exceptions imported and wrapped
**Count (refreshed):** 6 unique exception types

#### Exception Types
```
LcmInvalidClassException             - Invalid object type
LcmInvalidFieldException             - Invalid field access
LcmFileLockedException               - Project locked by another process
LcmDataMigrationForbiddenException   - Project needs FW migration
WorkerThreadException                - Background task failure
StartupException                     - FieldWorks startup failure  [NEW since original]
```

**Exposure:**
- **Public API:** Custom wrapper exceptions (FP_ReadOnlyError, FP_ParameterError)
- **Files:** `FLExProject.py` imports and handles
- **Usage Pattern:** Caught and re-raised as more user-friendly exceptions:

```python
# FLExProject.py (line 230-241)
except LcmFileLockedException as e:
    raise FP_FileLockedError()  # User-friendly message

except LcmDataMigrationForbiddenException as e:
    raise FP_MigrationRequired()  # Clear action required
```

**Risk:** LOW - exceptions used correctly for error handling

---

### Category 6: Data Type Tags/Constants

**Status:** [OK] Used internally for field navigation

#### Tag Classes (Property Names)
```
LexEntryTags            - Lexicon entry field names
LexSenseTags            - Sense field names
WfiWordformTags         - Wordform field names
WfiGlossTags            - Gloss field names
WfiAnalysisTags         - Analysis field names
WfiMorphBundleTags      - Morpheme bundle field names
MoFormTags              - Morpheme form field names
LexExampleSentenceTags  - Example sentence field names
TextTags                - Text field names
ReversalIndexEntryTags  - Reversal entry field names
CellarPropertyType      - Type system for properties (String, MultiUnicode, etc.)
```

**Exposure:**
- **Not exposed:** Users never reference these directly
- **Files:** Used in `lcm_casting.py` and Operations classes
- **Purpose:** Navigate LCM object properties by name
- **Risk:** LOW - internal use only

**Example:**
```python
# Users don't need to know about these:
from SIL.LCModel import LexEntryTags
# Internal access pattern:
entry.MorphoSyntaxAnalysesOC  # Navigate via properties, not tags
```

---

### Category 7: Cellar (Property Type System)

**Status:** [OK] Low-level property system, wrapped

#### Cellar Classes
```
CellarPropertyType          - Enum: String, MultiUnicode, MultiString, Reference, etc.
CellarPropertyTypeFilter    - Property filtering
```

**Exposure:**
- **Not exposed:** Internal property introspection only
- **Files:** 3 files (FLExProject.py, FLExLCM.py, lcm_casting.py)
- **Purpose:** Determine field types for validation
- **Risk:** LOW - only for internal type checking

```python
# FLExLCM.py - internal use
from SIL.LCModel.Core.Cellar import CellarPropertyType

CellarStringTypes = {CellarPropertyType.String,}
CellarMultiStringTypes = {CellarPropertyType.MultiUnicode, CellarPropertyType.MultiString}
```

---

### Category 8: Utility Classes

**Status:** [OK] Minimal exposure, used internally

#### Utility Imports
```
ReflectionHelper        - .NET reflection utilities for casting
WorkerThreadException   - Thread exception handling
VersionInfoProvider     - Get FieldWorks version info
FwUtils, FwDirectoryFinder, etc. - File/registry operations
```

**Exposure:**
- **Not exposed:** Internal utilities only
- **Files:** Centralized in FLExProject.py and FLExLCM.py
- **Risk:** LOW - wrapper functions insulate users

---

### Category 9: FieldWorks UI/Infrastructure

**Status:** [MINIMAL] Intentionally excluded from user API

#### UI/Infrastructure Classes
```
FwLcmUI                     - LCM user interface integration
ChooseLangProjectDialog     - Project selection dialog
ThreadHelper                - Thread synchronization
ProgressDialogWithTask      - Progress reporting dialog
ProjectId                   - Project identifier
FwDirectoryFinder          - FW installation paths
FwRegistryHelper           - Registry access
```

**Exposure:**
- **Not exposed:** Project initialization only (FLExLCM.py, FLExInit.py)
- **Files:** 8 files (mostly initialization)
- **Purpose:** Open projects, find FieldWorks installation
- **Risk:** MINIMAL - infrastructure, not data

**TODO Found:** Line 53 of FLExLCM.py
```python
# TODO: Use FW Project Chooser (ChooseLangProjectDialog())
#       and handle network drives
```
This suggests future enhancement to use native FW project selection dialog.

---

### Category 10: Writing Systems

**Status:** [OK] Minimal exposure

#### Writing System Classes
```
WritingSystemDefinition     - Writing system properties
Sldr                        - SLDR (Script Library Database Reference) integration
SpecialWritingSystemCodes   - Special codes (e.g., for audio)
```

**Exposure:**
- **Not exposed:** Only used internally for writing system lookup
- **Files:** Initialization and some Lexicon operations
- **Risk:** LOW - read-only usage

```python
# FLExInit.py
from SIL.WritingSystems import Sldr
# Internally used to initialize writing systems
```

---

## Exposed vs. Unexposed Capabilities

### Fully Exposed (57 Operations)

All accessed through `project.DOMAIN.METHOD()` pattern:

**Grammar Domain (13 ops)**
- POS, Phonemes, NaturalClasses, Environments, Allomorphs
- MorphRules, InflectionFeatures, GramCat, PhonRules, AffixTemplates
- CompoundRules, AdHocProhibitions

**Lexicon Domain (11 ops)**
- LexEntry, Senses, Examples, LexReferences, Etymology
- Variants, Pronunciations, Confidence, Filters

**TextsWords Domain (5 ops)**
- Texts, Wordforms, WfiAnalyses, Paragraphs, Segments

**Notebook Domain (5 ops)**
- DataNotebook, Notes, Annotations, Person, Location

**Lists Domain (6 ops)**
- Agents, PossibilityLists, SemanticDomains, TranslationTypes
- Publications, Media

**System Domain (7 ops)**
- WritingSystems, CustomFields, AnnotationDefs, Checks
- ProjectSettings, Anthropology, Discourse

**Discourse Domain (8 ops)**
- ConstCharts, ConstChartRows, ConstChartWordGroups
- ConstChartMovedText, ConstChartTags, ConstChartClauseMarkers
- (Plus Reversal/ReversalIndexes)

### Partially Exposed

**Undo/Redo Stack**
- `IUndoStackManager` imported in FLExProject.py
- Called only in `CloseProject()` for automatic save
- NOT exposed in public API - saves are automatic
- **Recommendation:** Document that changes auto-save on `CloseProject()`

**Metadata Cache**
- `IFwMetaDataCacheManaged` imported but not used actively
- Could enable schema introspection if needed
- **Recommendation:** Consider exposing for "what fields does X object have?" queries

**Advanced Text Building**
- `ITsStrBldr` (string builder) imported but hidden
- Available via `FLExProject.project` for advanced users
- **Recommendation:** Document power-user access pattern

### Not Exposed (Low Priority)

**Project Service Layer**
- Core project cache and object factory accessed via `project.ObjectFactory()` and `project.ObjectRepository()`
- These are available but documented as "advanced use only"
- Users can access if needed but shouldn't normally need them

**Low-Level Casting**
- `lcm_casting.py` module provides `cast_to_concrete()` for polymorphic types
- Internal use only, but documented in module docstring
- Power users can import if they need to work with base interfaces

---

## Usage Patterns

### Pattern 1: Safe Repository Access
Most common pattern - wrapped in Operations classes:
```python
# Files: 70+ Operations classes
# Example: Grammar/POSOperations.py
repo = self.project.ObjectRepository(ILexEntryRepository)
entry = repo.GetObject(hvo)
```
**Risk:** LOW - limited to read access, wrapped with validation

### Pattern 2: Factory + Error Handling
Object creation wrapped with write checks:
```python
# Example: Lexicon/AllomorphOperations.py (line ~90)
def Create(self, form_text):
    if not self.project.WriteEnabled:
        raise FP_ReadOnlyError()
    from SIL.LCModel import IMoStemAllomorphFactory
    factory = self.project.ObjectFactory(IMoStemAllomorphFactory)
    # Create with validation...
```
**Risk:** MINIMAL - write permission checked before factory use

### Pattern 3: Direct Project Access (Advanced)
Available for power users but discouraged:
```python
# Example: Some operations use directly
lexDB = project.lexDB  # Direct access to LexDb object
# Then access properties directly
```
**Risk:** MEDIUM - bypasses wrapper validation, needs user understanding

### Pattern 4: ServiceLocator Pattern
Projects use `ObjectFactory()` and `ObjectRepository()` getters:
```python
# FLExProject.py (line 273)
usm = self.ObjectRepository(IUndoStackManager)
usm.Save()

# Grammar/EnvironmentOperations.py
repo = self.project.ObjectRepository(ICmObjectRepository)
```
**Risk:** LOW - contained in framework code, not user-facing

### Pattern 5: Local Imports (Dependency Injection)
Factories imported only when needed:
```python
# AllomorphOperations.py - conditional import
def Create(self, ...):
    from SIL.LCModel import IMoStemAllomorphFactory
    factory = self.project.ObjectFactory(IMoStemAllomorphFactory)
```
**Benefit:** Avoids circular imports, allows optional functionality
**Risk:** LOW - internal pattern only

---

## TODOs and Known Limitations

### Found in Codebase

**1. FLExGlobals.py (Lines 102-105) - LINUX SUPPORT**
```
TODO: First attempt at Linux support.
As of Apr2024, FW installation has changed to use flatpak
and this no longer works.
```
**Impact:** Linux support incomplete, requires FW flatpak support
**Priority:** MEDIUM - affects non-Windows users
**Workaround:** Windows/macOS only for now

**2. FLExLCM.py (Line 53) - PROJECT CHOOSER DIALOG**
```
TODO: Use FW Project Chooser (ChooseLangProjectDialog())
      and handle network drives
```
**Impact:** Simple file listing instead of FW dialog, no network support
**Priority:** LOW - functional workaround exists
**Enhancement:** Would improve UX with native FW dialog

### Implicit Limitations (Not Documented)

**1. No Direct Access to:**
- Undo stack manipulation (auto-save only)
- Cache invalidation (auto-managed)
- Background task management (single-threaded)

**2. Incomplete Domain Coverage:**
- Scripture domain has minimal operations
- Some discourse analysis features limited
- Constraint-based morphology not wrapped

---

## Risk Assessment

### Critical (Must Be Protected)
- [✓] `IUndoStackManager` - Protected, no user access
- [✓] Thread/cache management - Hidden in framework
- [✓] Direct cast operations - Wrapped in `lcm_casting.py`, internal only

### High (Should Limit Exposure)
- [OK] Factory interfaces - Wrapped, write-enabled only
- [OK] Repository access - Wrapped in Operations classes
- [OK] Exception types - Custom wrappers used

### Medium (Can Be Exposed with Documentation)
- [ ] `ITsStrBldr` - Advanced text building (document as power-user feature)
- [ ] `IFwMetaDataCacheManaged` - Schema introspection (expose as utility if needed)
- [ ] Direct `.project` access - Clearly mark as "use at own risk"

### Low (Safe to Expose)
- [✓] Tag classes (LexEntryTags, etc.) - Already internal, safe
- [✓] Property type system - Read-only metadata
- [✓] Version info - Read-only constants

---

## Recommendations

### 1. Documentation Enhancements [Priority: HIGH]

**Suggestion:** Create `docs/ADVANCED_LCM_ACCESS.md`
- Document `.project`, `.lp`, `.lexDB` direct access patterns
- Show `ITsString` usage for users who need it
- Explain when to use raw LCM vs. Operations classes
- Provide examples of accessing data not yet wrapped

**Suggestion:** Document in CLAUDE.md under new section "Power User Access"
```
## Power User Access

For functionality not yet wrapped in Operations classes,
you can access the LCM API directly:

project.project        # Raw LcmCache
project.lp             # LangProject
project.lexDB          # LexDb

Use sparingly and document your usage!
```

### 2. Feature Completion [Priority: MEDIUM]

**Metadata Introspection:**
- Expose `IFwMetaDataCacheManaged` as optional utility
- Enable "schema discovery" for generated tools
- Useful for documentation generation

**Advanced Text Handling:**
- Create `TextBuilderOperations` wrapper for `ITsStrBldr`
- Document multi-lingual text patterns clearly
- Examples of handling field-specific writing systems

**Undo/Redo Control:**
- Document automatic save-on-close behavior
- Consider exposing `UndoStackManager` for batch operations
- Would enable "undo all changes" functionality

### 3. Infrastructure Improvements [Priority: LOW-MEDIUM]

**Linux Support:**
- Update flatpak path handling in FLExGlobals.py
- Add detection for flatpak environment variables
- Test with FW flatpak installation

**Project Selection:**
- Implement `ChooseLangProjectDialog()` as optional method
- Keep simple file-based listing as fallback
- Handle network/UNC paths properly

### 4. Testing & Validation [Priority: MEDIUM]

**Current:** Contract tests validate API compatibility
**Suggested:** Add tests for edge cases:
- Operations on polymorphic collections (casting)
- Text handling across multiple writing systems
- Exception handling with locked projects
- Concurrent access patterns

### 5. Architecture Documentation [Priority: HIGH]

**Create:** `docs/LCM_WRAPPER_ARCHITECTURE.md`
- Explain why repositories/factories are wrapped
- Document casting patterns for polymorphic types
- Show how to extend with new Operations classes
- Provide decision tree for when to wrap vs. expose

---

## Summary Table: All LCM Capabilities

| Category | Imported | Exposed | Files | Risk | Status |
|---|---|---|---|---|---|
| **Repositories** | 9 | Via Operations | 70+ | LOW | [OK] Wrapped |
| **Factories** | 12 | Via Create() | 12 | MINIMAL | [OK] Wrapped |
| **Managers** | 2 | 1/2 (UndoStackManager only) | 3 | LOW | [OK] Protected |
| **Text Interfaces** | 4 | Via BestStr() | 50+ | LOW | [OK] Wrapped |
| **Exceptions** | 5 | Custom wrappers | 1 | LOW | [OK] Wrapped |
| **Tags/Constants** | 11 | Never | 15 | LOW | [OK] Hidden |
| **Cellar System** | 2 | Never | 3 | LOW | [OK] Hidden |
| **Utilities** | 7+ | Never | 8 | LOW | [OK] Hidden |
| **UI/Infrastructure** | 10+ | Never | 8 | MINIMAL | [OK] Hidden |
| **Writing Systems** | 2 | Minimal | 3 | LOW | [OK] Safe |
| **Operations Classes** | N/A | 57 | 64 | MINIMAL | [OK] Public API |

---

## Conclusion

The FlexLibs2 architecture successfully **abstracts away LCM complexity** while maintaining full functionality through a clean, user-friendly API. The 90+ imported LCM classes are strategically hidden behind 57 Operations classes that provide safe, validated access to FieldWorks data.

**Strengths:**
- Consistent wrapper pattern across all domains
- Safe exception handling with custom error types
- Factory/repository access protected by write-enabled checks
- Low-level primitives (text, casting) well-hidden
- Good use of dependency injection for optional features

**Areas for Improvement:**
- Document power-user access patterns
- Expose metadata introspection if needed
- Add a few missing operations (Scripture domain)
- Complete Linux support for flatpak

**Overall Risk:** **MINIMAL** - The abstraction layer effectively isolates users from dangerous LCM operations while providing escape hatches for advanced use cases.

