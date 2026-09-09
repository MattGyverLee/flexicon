# LCM Capabilities Audit - Executive Summary

**Audit Date:** 2026-05-27
**Scope:** 106 Python files in `flexicon/code/`
**Status:** REFRESHED — Ready for review

## Quick Overview

This audit analyzes **14 SIL namespaces** imported across **73 files** in the flexicon codebase, totalling **569 import statements** over **233 unique classes/interfaces**, organized behind **60 user-facing Operations classes** (plus the `BaseOperations` parent).

### Key Numbers

| Metric | Count |
|---|---|
| Total Python files analyzed | 106 |
| Files with SIL imports | 73 |
| Distinct SIL namespaces imported | 14 |
| LCM import statements | 569 |
| Unique classes/interfaces imported | 233 |
| User-facing Operations classes | 60 (+ BaseOperations) |
| Helper/Infrastructure files | 7 |
| TODOs found | 2 |
| Critical risks identified | 0 |

> Delta vs. 2025-03-16 audit: 101 -> 106 files; 72 -> 73 files with SIL imports; 90+ -> 233 unique imports counted; 57 -> 60 Operations classes; 9 -> 18 repositories; 12 -> 74 factories (the original number was a lower-bound from spot inspection; the refreshed number is exhaustive).

---

## The Architecture in 30 Seconds

Flexicon uses a **Repository -> Factory -> Wrapper** pattern:

```
Users
  v
FLExProject.DOMAIN.METHOD()        <- 60 Operations classes
  v
Repository/Factory/Manager         <- Wrapped LCM APIs
  v
SIL.LCModel (233 classes)          <- FieldWorks internals
```

**Result:** Users never touch the raw LCM API. Everything is safe, validated, and documented.

---

## What's Imported

### The 14 SIL Namespaces

| Namespace | Unique classes | Files using | Purpose |
|---|---:|---:|---|
| `SIL.LCModel` | 203 | 64 | Core data interfaces, factories, repositories, tags |
| `SIL.LCModel.Core.KernelInterfaces` | 5 | 62 | Text interfaces (ITsString, IMultiString, ...) |
| `SIL.LCModel.Core.Text` | 1 | 57 | TsStringUtils text helpers |
| `SIL.LCModel.Core.Cellar` | 3 | 3 | Property type system |
| `SIL.LCModel.Infrastructure` | 2 | 2 | IDataReader, IFwMetaDataCacheManaged |
| `SIL.LCModel.Utils` | 2 | 2 | ReflectionHelper, WorkerThreadException |
| `SIL.LCModel.Application.ApplicationServices` | 2 | 2 | XmlList, XmlTranslatedLists |
| `SIL.LCModel.DomainServices` | 2 | 1 | MsaType, SandboxGenericMSA |
| `SIL.FieldWorks.Common.FwUtils` | 7 | 4 | FwUtils, FwDirectoryFinder, ThreadHelper, ... |
| `SIL.FieldWorks.Common.Controls` | 1 | 1 | ProgressDialogWithTask |
| `SIL.FieldWorks.FdoUi` | 1 | 1 | FwLcmUI |
| `SIL.FieldWorks.FwCoreDlgs` | 1 | 1 | ChooseLangProjectDialog |
| `SIL.FieldWorks` | 1 | 1 | ProjectId |
| `SIL.WritingSystems` | 2 | 3 | Sldr, WritingSystemDefinition |

### Categories at a Glance

**Data Access (Repositories — 18 unique)**
```
ICmObjectRepository, ICmPossibilityRepository, ICmPersonRepository,
ICmAnnotationDefnRepository, ILexEntryRepository, ILexEntryTypeRepository,
ILexSenseRepository, ILexRefTypeRepository, ITextRepository,
ISegmentRepository, IStTxtParaRepository, IWfiWordformRepository,
IWfiAnalysisRepository, IWfiGlossRepository, IReversalIndexRepository,
IRnResearchNbkRepository, IDsConstChartRepository, IScrBookRepository
```

**Object Creation (Factories — 74 unique)**
A non-exhaustive sample: `ICmPossibilityListFactory`, `IPartOfSpeechFactory`, `IPhEnvironmentFactory`, `IMoStemAllomorphFactory`, `IMoAffixAllomorphFactory`, `IStTextFactory`, `IStTxtParaFactory`, `ILexEntryRefFactory`, `ILexEntryFactory`, `ILexSenseFactory`, `IDsConstChartFactory`, `IDsDiscourseDataFactory`, `IConstChartRowFactory`, `IConstChartWordGroupFactory`, `IConstChartMovedTextMarkerFactory`, `IConstChartTagFactory`, `IConstChartClauseMarkerFactory`, `IPhRegularRuleFactory`, `IPhMetathesisRuleFactory`, `IPhReduplicationRuleFactory`, `IMoEndoCompoundFactory`, `IMoExoCompoundFactory`, `IMoInflAffixTemplateFactory`, `IMoInflClassFactory`, `IScrBookFactory`, `IScrDraftFactory`, `IScrSectionFactory`, `IScrTxtParaFactory`, `IScrScriptureNoteFactory`, `IScrBookAnnotationsFactory`, `IRnGenericRecFactory`, `IReversalIndexFactory`, `IReversalIndexEntryFactory`, `IWfiWordformFactory`, `IWfiAnalysisFactory`, `IWfiGlossFactory`, `IWfiMorphBundleFactory`, plus 35+ more. See `LCM_CAPABILITIES_AUDIT_REFERENCES.md` for the full list.

**Text Handling**
```
SIL.LCModel.Core.KernelInterfaces
- ITsString (immutable text)
- ITsStrBldr (mutable text builder)
- IMultiUnicode, IMultiString
- FwObjDataTypes

SIL.LCModel.Core.Text
- TsStringUtils (text utilities)
```

**Services & Management**
```
SIL.LCModel
- IUndoStackManager (save operations)
- IFwMetaDataCacheManaged (schema)

SIL.LCModel.Infrastructure
- IDataReader (advanced)
- IFwMetaDataCacheManaged
```

**System/Metadata**
```
SIL.LCModel.Core.Cellar
- CellarPropertyType
- CellarPropertyTypeFilter

SIL.LCModel (constants, tags)
- LexEntryTags, LexSenseTags, LexEntryRefTags, LexRefTypeTags,
  LexExampleSentenceTags, WfiWordformTags, WfiAnalysisTags,
  WfiGlossTags, WfiMorphBundleTags, MoFormTags, MoMorphTypeTags,
  TextTags, ReversalIndexEntryTags
- LcmCache, LcmSettings, LcmFileHelper, GenDate, Opinions,
  SpecialWritingSystemCodes
- Exception types (see below)
```

**FieldWorks Integration**
```
SIL.FieldWorks.*
- ProjectId
- FwLcmUI (user interface integration)
- ChooseLangProjectDialog
- FwDirectoryFinder, FwRegistryHelper, FwUtils, FwAppArgs (paths/args)
- ThreadHelper, ProgressDialogWithTask, VersionInfoProvider, StartupException

SIL.WritingSystems
- WritingSystemDefinition
- Sldr (language data)
```

**Exceptions (6 unique)**
```
LcmFileLockedException, LcmDataMigrationForbiddenException,
LcmInvalidClassException, LcmInvalidFieldException,
WorkerThreadException, StartupException
```
> Delta: original audit listed 5. The refresh confirms a 6th (`StartupException` from `SIL.FieldWorks.Common.FwUtils`).

---

## Exposure Matrix

### Fully Exposed (User-Facing API)

**60 Domain Operations** - All accessed via `project.DOMAIN` property:

```python
# Grammar (9 ops)
project.POS
project.Phonemes
project.Environments
project.Allomorphs       # in Lexicon, but related
project.MorphRules
project.PhonRules
project.NaturalClasses
project.GramCat
project.InflectionFeatures
project.PhonFeatures

# Lexicon (10 ops)
project.LexEntry
project.Senses
project.Examples
project.LexReferences
project.MSA
project.Etymology
project.Pronunciations
project.Variants
project.SemanticDomains
project.Allomorphs

# TextsWords (8 ops)
project.Texts
project.Wordforms
project.WfiAnalyses
project.WfiGlosses
project.WfiMorphBundles
project.Paragraphs
project.Segments
project.Discourse       # legacy alias

# Lists (6 ops)
project.PossibilityLists, project.Publications, project.TranslationTypes,
project.Agents, project.Confidence, project.Overlays

# Notebook (5 ops)
project.DataNotebook, project.Notes, project.Person, project.Location,
project.Anthropology

# Scripture (6 ops)
project.ScrBook, project.ScrDraft, project.ScrSection, project.ScrTxtPara,
project.ScrAnnotations, project.ScrNote  # accessed via Scripture operations

# Discourse (7 ops)
project.ConstCharts, project.ConstChartRows, project.ConstChartWordGroups,
project.ConstChartMovedText, project.ConstChartMarkers,
project.ConstChartCellTags, project.ConstChartClauseMarkers

# Reversal (2 ops)
project.ReversalIndexes, project.ReversalEntries

# System (5 ops)
project.WritingSystems, project.CustomFields, project.AnnotationDefs,
project.Checks, project.ProjectSettings

# Shared (2 ops)
project.Filters, project.Media
```

Each exposes methods like:
```python
.GetAll()          # List all items
.Find(name)        # Find by name
.Create(...)       # Create new item
.Update(...)       # Modify item
.Delete(item)      # Remove item
```

### Partially Exposed

| Feature | Imported | Exposed | Notes |
|---|---|---|---|
| Undo/Redo | IUndoStackManager | YES (since refresh) | `project.Undo()` and `project.Redo()` now available; auto-save on `CloseProject()` retained |
| Metadata | IFwMetaDataCacheManaged | NO | Imported but not actively wired through Operations |
| Advanced Text | ITsStrBldr | NO | Hidden, available via `.project` for power users |
| Direct Access | .project, .lp, .lexDB | YES | Available but discouraged |

### Not Exposed (Internal Only)

| Category | Count | Examples |
|---|---|---|
| Repository/Factory bases | 90+ (74 factories + 18 repos) | Wrapped behind Operations methods |
| Text tags | 13 | LexEntryTags, TextTags, ReversalIndexEntryTags, etc. |
| Property system | 3 | CellarPropertyType, CellarPropertyTypeFilter |
| Utilities | 6 | ReflectionHelper, ThreadHelper, FwUtils, FwRegistryHelper, LcmFileHelper, TsStringUtils |
| UI/Infrastructure | 10+ | Dialogs, file finders, registry, ProjectId |

---

## Risk Assessment

### Critical Risks: **NONE FOUND**

Dangerous operations are all protected:
- Undo stack: Now exposed via dedicated `Undo()`/`Redo()` methods (added since original audit), still internally guarded
- Cache management: Hidden, auto-managed
- Thread handling: Infrastructure only
- Direct casting: Wrapped, marked as internal

### Medium Risks: **2 IDENTIFIED**

1. **Direct `.project` access** (discouraged but allowed)
   - Users can bypass wrappers if they try hard
   - Mitigation: Document as "use at own risk"
   - Current status: Not advertised, available in docstring example only

2. **Incomplete domain coverage**
   - Original audit flagged Scripture and Discourse. Discourse coverage is now strong (7 Operations). Scripture has grown from 2 to 6 Operations but several Scripture features remain unwrapped.
   - Mitigation: Document workarounds
   - Current status: Known limitation, accept as-is for now

### Low Risks: **HANDLED**

- Text string handling (ITsString) - wrapped in `BestStr()`
- Exception mapping - custom exceptions hide LCM errors
- Factory calls - all guarded by write-enabled checks
- Repository access - wrapped in safe query methods

---

## Recommendations Summary

### 1. Immediate (High Priority)

**[DOCUMENT]** Create `docs/ADVANCED_LCM_ACCESS.md`
- How to use `.project` for advanced patterns
- When to use raw LCM vs. Operations
- ITsString examples for power users

**[UPDATE]** Add to CLAUDE.md: "Power User Access" section
- Brief guide to bypassing wrappers safely
- Examples of accessing unexposed features

### 2. Short Term (Medium Priority)

**[IMPLEMENT]** Expose `IFwMetaDataCacheManaged`
- Enable "what fields does X have?" queries
- Useful for introspection and documentation

**[IMPLEMENT]** Create `TextBuilderOperations` wrapper
- Wrap ITsStrBldr for complex text building
- Document multi-writing-system patterns

**[COMPLETE]** Scripture domain operations
- Several Scripture features added since original audit (ScrBook, ScrDraft, ScrSection, ScrTxtPara, ScrAnnotations, ScrNote) but coverage still incomplete

### 3. Long Term (Low Priority)

**[ENHANCE]** Linux flatpak support
- Update FLExGlobals.py path detection
- Test with FW flatpak installation

**[ENHANCE]** Project selection dialog
- Use native `ChooseLangProjectDialog()`
- Support network drives

---

## What Should Be Wrapped vs. Not

### Should Always Be Wrapped
- Factories (object creation)
- Write operations (write-enabled checks)
- Complex queries (validation)
- Text handling (multi-lingual support)

### Should NOT Be Wrapped
- Read-only metadata
- Constants/enumerations
- Version information
- Configuration data

### Should Be Exposed (for power users)
- [ ] IFwMetaDataCacheManaged (schema introspection)
- [ ] ITsStrBldr (complex text building)
- [ ] Direct repository access (optional, documented)

---

## File Organization

```
flexicon/code/                                   (106 .py files)
- FLExProject.py                <- User API entry point (~95 properties)
- BaseOperations.py             <- Parent class for all operations
- FLExInit.py                   <- Initialization
- FLExLCM.py                    <- Project opening
- FLExGlobals.py                <- FW paths and globals
- lcm_casting.py                <- Type casting utilities (INTERNAL)
- CastingOperations.py          <- Casting for operations (INTERNAL)
- PythonicWrapper.py            <- Suffix-free property access (INTERNAL)
- (other infrastructure files)

- Grammar/                      <- 9 Operations classes
    POSOperations.py, PhonemeOperations.py, EnvironmentOperations.py,
    PhonologicalRuleOperations.py, NaturalClassOperations.py,
    GramCatOperations.py, MorphRuleOperations.py,
    InflectionFeatureOperations.py, PhonFeatureOperations.py

- Lexicon/                      <- 10 Operations classes
    LexEntryOperations.py, LexSenseOperations.py, AllomorphOperations.py,
    ExampleOperations.py, LexReferenceOperations.py, MSAOperations.py,
    EtymologyOperations.py, PronunciationOperations.py,
    SemanticDomainOperations.py, VariantOperations.py

- TextsWords/                   <- 8 Operations classes
    TextOperations.py, WordformOperations.py, WfiAnalysisOperations.py,
    WfiGlossOperations.py, WfiMorphBundleOperations.py,
    ParagraphOperations.py, SegmentOperations.py, DiscourseOperations.py

- Notebook/                     <- 5 Operations classes
    DataNotebookOperations.py, NoteOperations.py, PersonOperations.py,
    LocationOperations.py, AnthropologyOperations.py

- Lists/                        <- 6 Operations classes
    AgentOperations.py, PossibilityListOperations.py,
    PublicationOperations.py, TranslationTypeOperations.py,
    ConfidenceOperations.py, OverlayOperations.py

- System/                       <- 5 Operations classes
    AnnotationDefOperations.py, CheckOperations.py,
    CustomFieldOperations.py, ProjectSettingsOperations.py,
    WritingSystemOperations.py

- Discourse/                    <- 7 Operations classes
    ConstChartOperations.py, ConstChartRowOperations.py,
    ConstChartWordGroupOperations.py, ConstChartMovedTextOperations.py,
    ConstChartMarkerOperations.py, ConstChartCellTagOperations.py,
    ConstChartClauseMarkerOperations.py

- Reversal/                     <- 2 Operations classes
    ReversalIndexOperations.py, ReversalIndexEntryOperations.py

- Scripture/                    <- 6 Operations classes (up from 2)
    ScrBookOperations.py, ScrDraftOperations.py, ScrSectionOperations.py,
    ScrTxtParaOperations.py, ScrAnnotationsOperations.py,
    ScrNoteOperations.py

- Shared/                       <- 2 Operations + utilities
    FilterOperations.py, MediaOperations.py,
    string_utils.py, smart_collection.py, wrapper_base.py
```

---

## TODOs in Code

### TODO #1: Linux Flatpak Support
- **File:** `flexicon/code/FLExGlobals.py:103`
- **Issue:** Old path logic doesn't work with flatpak (FW Apr2024+ migration)
- **Current:** Windows/macOS only
- **Effort:** LOW - Detection + path fallback
- **Impact:** MEDIUM - Linux users need workaround
- **Status:** Still open since original audit

### TODO #2: Use FW Project Chooser
- **File:** `flexicon/code/FLExLCM.py:59`
- **Issue:** Using simple file listing, not FW native dialog
- **Current:** Works but not user-friendly
- **Effort:** LOW - Use existing dialog class
- **Impact:** LOW - Cosmetic enhancement
- **Status:** Still open since original audit

---

## Testing & Quality

**Current Coverage:**
- Contract tests validate API compatibility
- Operations classes follow consistent patterns
- Casting operations thoroughly tested

**Recommended Additions:**
- Edge case tests for polymorphic collections
- Multi-writing-system text handling
- Locked project exception handling
- Concurrent access patterns

---

## Usage Examples

### User-Level (Safe)
```python
from flexicon.code.FLExProject import FLExProject

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

# All safe - wrapped and validated
for pos in project.POS.GetAll():
    print(project.POS.GetName(pos))

entry = project.LexEntry.Create("run", "stem")
sense = project.LexEntry.AddSense(entry, "to move")

project.CloseProject()
```

### Power User (Documented but Not Recommended)
```python
# Direct repository access (available in docstrings)
repo = project.ObjectRepository(ICmObjectRepository)
obj = repo.GetObject(hvo)

# Text building with ITsString
from SIL.LCModel.Core.Text import TsStringUtils
ws_handle = project.WSHandle('en')
ts = TsStringUtils.MakeString("text", ws_handle)

# Type casting
from flexicon.code.lcm_casting import cast_to_concrete
concrete = cast_to_concrete(base_interface_obj)
```

---

## Conclusion

**The LCM audit reveals a well-designed abstraction layer that:**

1. **Successfully hides complexity** - 233 LCM classes wrapped in 60 user-friendly Operations
2. **Protects users** - Write operations guarded, exceptions mapped, factories validated
3. **Allows escape hatches** - Power users can access raw LCM if documented properly
4. **Maintains consistency** - Repository -> Factory -> Wrapper pattern throughout
5. **Has minimal risk** - No critical security/stability concerns found

**The main improvement area is documentation** - Adding guides for:
- Power user access patterns
- Advanced text handling
- Schema introspection
- When to wrap new features

**Overall Assessment: HEALTHY ARCHITECTURE**

The project successfully achieves its goal of making FLEx data accessible without overwhelming users with LCM complexity. The separation of concerns is clean, and the abstraction layers are appropriate to the task. Growth since the original audit is healthy: Operations classes grew from 57 to 60, with substantial new coverage in Discourse (8 ops) and Scripture (6 ops), without compromising the abstraction layer.

---

## Document References

- **LCM_CAPABILITIES_AUDIT.md** - Comprehensive import analysis
- **LCM_CAPABILITIES_AUDIT_REFERENCES.md** - Code file and line references
- **LCM_AUDIT_SUMMARY.md** - This executive summary

---

**Audit Date:** 2026-05-27 (refreshed from 2025-03-16)
**Scope:** flexicon/code directory (106 Python files)
**Methodology:** Automated import extraction via `tools/extract_api_usage.py` + manual usage-pattern review
**Confidence Level:** HIGH - All 569 import statements traced, all 60 Operations documented
