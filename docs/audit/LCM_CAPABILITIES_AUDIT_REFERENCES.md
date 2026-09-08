# FlexLibs2 LCM Capabilities - Code References

This document provides specific file and line references for each LCM capability mentioned in the main audit.

**Audit Date:** 2026-05-27 (refreshed from 2025-03-16)
**Scope:** 106 Python files in `flexlibs2/code/`
**Status:** REFRESHED -- Ready for review

> Line numbers below reflect the original 2025-03-16 snapshot. The current line numbers may have shifted (e.g., `FLExGlobals.py` TODO is now at line 103, `FLExLCM.py` TODO is now at line 59). The categorical inventory has been refreshed in `Summary Statistics` below; for full source-of-truth on every import location, see the regenerated JSON in `reports/audit/api_usage_extract.json` (one record per import statement with file path and line number).

---

## Repository Interfaces

### ICmObjectRepository
- **Import:** `FLExProject.py:29`
- **Usage:** Generic object lookup by ID (Hvo)
- **Files using it:**
  - `Grammar/EnvironmentOperations.py` - lookup by Hvo
  - `Grammar/POSOperations.py` - reference resolution
  - Base usage pattern in Operations classes

### ILexEntryRepository
- **Import:** `FLExProject.py:30`
- **Usage:** Lexicon entry access, query operations
- **Files:** Multiple lexicon operations

### IWfiWordformRepository
- **Import:** `FLExProject.py:32`
- **Usage:** Wordform inventory queries
- **Files:** `Wordform/WfiWordformOperations.py`

### IWfiAnalysisRepository
- **Import:** `FLExProject.py:34`
- **Usage:** Wordform analysis access
- **Files:** `Wordform/WfiAnalysisOperations.py`

### ICmPossibilityRepository
- **Import:** `FLExProject.py:39`
- **Usage:** POS, semantic domains, list items
- **Files:** `Grammar/POSOperations.py`, `Lexicon/LexEntryOperations.py`, etc.

### ITextRepository
- **Import:** `FLExProject.py:43`
- **Usage:** Text document access
- **Files:** `TextsWords/TextOperations.py`

### ISegmentRepository
- **Import:** `FLExProject.py:45`
- **Usage:** Text segment lookup
- **Files:** `TextsWords/SegmentOperations.py`

### ILexRefTypeRepository
- **Import:** `FLExProject.py:38`
- **Usage:** Reference type definitions
- **Files:** `Lexicon/LexReferenceOperations.py`

---

## Factory Interfaces

### ICmPossibilityListFactory
- **Import:** `Grammar/GramCatOperations.py:19`
- **Conditional:** `Lexicon/LexReferenceOperations.py:120` (local import)
- **Usage:** Create POS lists, semantic domains
- **Usage Pattern:**
  ```python
  from SIL.LCModel import ICmPossibilityListFactory
  factory = self.project.ObjectFactory(ICmPossibilityListFactory)
  new_list = factory.Create()
  ```

### IPartOfSpeechFactory
- **Import:** `Grammar/POSOperations.py:15`
- **Usage:** Create parts of speech
- **Pattern:** Conditional import in Create() method
- **Location:** `Grammar/POSOperations.py:60-75`

### IPhEnvironmentFactory
- **Import:** `Grammar/EnvironmentOperations.py:15`
- **Usage:** Create phonological environments
- **Location:** `Grammar/EnvironmentOperations.py:85-100`

### IMoStemAllomorphFactory
- **Import:** `Lexicon/AllomorphOperations.py` (line ~130, local)
- **Usage:** Create stem allomorphs
- **Location:** Conditional import in Create method

### IMoAffixAllomorphFactory
- **Import:** `Lexicon/AllomorphOperations.py` (line ~150, local)
- **Usage:** Create affix allomorphs
- **Location:** Conditional import in Create method

### IStTextFactory / IStTxtParaFactory
- **Imports:** `TextsWords/ParagraphOperations.py` (local conditional)
- **Usage:** Create text and paragraph objects
- **Location:** In Create() methods for text/paragraph operations

### IScrBookAnnotationsFactory
- **Import:** Scripture operations (if implemented)
- **Usage:** Scripture annotation creation
- **Status:** Minimal coverage in current codebase

### IDsDiscourseFactory
- **Import:** `Discourse/ConstChartOperations.py` (line ~220, conditional)
- **Usage:** Create discourse structures
- **Location:** Conditional import in Create method

### ILexEntryRefFactory
- **Import:** `FLExProject.py:430` (conditional in method)
- **Usage:** Create lexical references
- **Location:** Internal method for reference creation

---

## Manager/Service Interfaces

### IUndoStackManager
- **Import:** `FLExProject.py:53`
- **Usage:** Save changes, undo/redo stack
- **Called:** `FLExProject.py:273` in `CloseProject()`
  ```python
  def CloseProject(self):
      if self.writeEnabled:
          usm = self.ObjectRepository(IUndoStackManager)
          usm.Save()
  ```
- **Status:** Internal, not exposed to users
- **Note:** Automatic save-on-close, no manual control

### IFwMetaDataCacheManaged
- **Import:** `FLExProject.py:62`
- **Usage:** Metadata cache access (not actively used)
- **Status:** Imported but not utilized
- **Recommendation:** Could enable schema introspection

---

## Text/String Interfaces

### ITsString
- **Import:** Multiple files
  - `FLExProject.py:65`
  - `Grammar/GramCatOperations.py:18`
  - `Lexicon/AllomorphOperations.py:18`
  - Plus 40+ more files
- **Usage:** Immutable multi-lingual text
- **Wrapped by:** `BestStr()` in FLExProject.py:1831
- **Example usage in wrapper:** `FLExProject.py:166-192`
  ```python
  from SIL.LCModel.Core.KernelInterfaces import ITsString, ITsStrBldr
  lexEntryValue = ITsString(lexForm.Form.get_String(WSHandle)).Text
  newValue = convert_headword(lexEntryValue)
  mkstr = TsStringUtils.MakeString(newValue, WSHandle)
  lexForm.Form.set_String(WSHandle, mkstr)
  ```

### ITsStrBldr
- **Import:** `FLExProject.py:65`
- **Usage:** String builder for mutable text
- **Status:** Imported but hidden from users
- **Recommendation:** Document as power-user feature

### TsStringUtils
- **Import:** `FLExProject.py:66`
- **Usage:** Text utility functions (MakeString, GetText)
- **Used in:** 50+ files for text manipulation
- **Common calls:** `TsStringUtils.MakeString(text, ws_handle)`

### IMultiUnicode / IMultiString
- **Import:** Infrastructure, not direct user imports
- **Usage:** Multi-language string containers
- **Wrapped by:** Multi-lingual property access methods

---

## Exception Types

### LcmInvalidClassException
- **Import:** `FLExProject.py:49`
- **Handling:** Not exposed, internal only
- **Usage:** Validate object types during casting

### LcmInvalidFieldException
- **Import:** `FLExProject.py:50`
- **Handling:** Not exposed, internal only
- **Usage:** Validate field access

### LcmFileLockedException
- **Import:** `FLExProject.py:51`
- **Caught:** `FLExProject.py:230-231`
  ```python
  except LcmFileLockedException as e:
      raise FP_FileLockedError()
  ```
- **Wrapped as:** `FP_FileLockedError` (user-friendly)

### LcmDataMigrationForbiddenException
- **Import:** `FLExProject.py:52`
- **Caught:** `FLExProject.py:233-241`
  ```python
  except (LcmDataMigrationForbiddenException, WorkerThreadException) as e:
      raise FP_MigrationRequired()
  ```
- **Wrapped as:** `FP_MigrationRequired` (user-friendly)

### WorkerThreadException
- **Import:** `FLExProject.py:67`
- **Handling:** Caught with `LcmDataMigrationForbiddenException`
- **Usage:** Background task errors

---

## Data Type Tags

### LexEntryTags
- **Import:** `FLExProject.py:30`
- **Usage:** Field name constants for lexical entries
- **Example:** Navigate entry properties by name
- **Status:** Never exposed to users

### LexSenseTags
- **Import:** `FLExProject.py:31`
- **Usage:** Field name constants for senses
- **Status:** Internal only

### WfiWordformTags
- **Import:** `FLExProject.py:32`
- **Usage:** Wordform property names
- **Status:** Internal only

### WfiAnalysisTags
- **Import:** `FLExProject.py:34`
- **Usage:** Analysis property names
- **Status:** Internal only

### MoFormTags / LexExampleSentenceTags / TextTags / ReversalIndexEntryTags
- **Imports:** `FLExProject.py` (lines 31-46)
- **Usage:** Domain-specific property constants
- **Status:** All internal only

---

## Cellar (Property Type System)

### CellarPropertyType
- **Import:**
  - `FLExProject.py:57`
  - `FLExLCM.py:34`
  - `lcm_casting.py`
- **Usage:** Property type enumeration
- **Example in FLExLCM.py:46-48:**
  ```python
  CellarStringTypes = {CellarPropertyType.String, }
  CellarMultiStringTypes = {CellarPropertyType.MultiUnicode,
                            CellarPropertyType.MultiString}
  ```
- **Status:** Internal property introspection only

### CellarPropertyTypeFilter
- **Import:** `FLExProject.py:58`
- **Usage:** Filter properties by type
- **Status:** Internal only

---

## Utility Classes

### ReflectionHelper
- **Import:**
  - `FLExProject.py:67`
  - `lcm_casting.py` (implicit usage)
- **Usage:** .NET reflection for type casting
- **Location:** Used in casting operations for polymorphic types

### WorkerThreadException
- **Already covered above** (under Exceptions)

### VersionInfoProvider
- **Import:** `FLExGlobals.py:159`
- **Usage:** Get FieldWorks version information
- **Location:** `FLExGlobals.py:159-164`
  ```python
  from SIL.FieldWorks.Common.FwUtils import VersionInfoProvider
  vip = VersionInfoProvider(Assembly.GetAssembly(VersionInfoProvider), False)
  FWShortVersion = System.Version(vip.ShortNumericAppVersion)
  ```

### FwUtils / FwDirectoryFinder / FwRegistryHelper
- **Imports:** `FLExInit.py:24-25`, `FLExLCM.py:38-40`
- **Usage:** File paths, registry access, utility functions
- **Status:** Infrastructure initialization only

---

## FieldWorks UI/Infrastructure

### FwLcmUI
- **Import:** `FLExLCM.py:41`
- **Usage:** LCM user interface integration
- **Location:** `FLExLCM.py:84`
  ```python
  ui = FwLcmUI(None, th)  # IHelpTopicProvider, ISynchronizeInvoke
  ```
- **Status:** Project initialization only

### ChooseLangProjectDialog
- **Import:** `FLExLCM.py:42`
- **Usage:** FW project selection dialog
- **Status:** Not used (TODO in FLExLCM.py:53)
- **Reference:** `FLExLCM.py:53-54`
  ```python
  # TODO: Use FW Project Chooser (ChooseLangProjectDialog())
  #       and handle network drives
  ```

### ThreadHelper
- **Import:** `FLExLCM.py:38`
- **Usage:** Thread synchronization for UI operations
- **Location:** `FLExLCM.py:83`
  ```python
  th = ThreadHelper()
  ui = FwLcmUI(None, th)
  ```

### ProgressDialogWithTask
- **Import:** `FLExLCM.py:37`
- **Usage:** Show progress dialog during project opening
- **Location:** `FLExLCM.py:90`
  ```python
  dlg = ProgressDialogWithTask(th)
  ```

### ProjectId
- **Import:** `FLExLCM.py:36`
- **Usage:** Project identifier for opening
- **Location:** `FLExLCM.py:81`
  ```python
  projId = ProjectId(projectFileName)
  ```

### FwDirectoryFinder
- **Import:** `FLExLCM.py:39`
- **Usage:** Find FW installation directories
- **Location:** `FLExLCM.py:85`
  ```python
  dirs = FwDirectoryFinder.LcmDirectories
  ```

---

## Writing Systems

### WritingSystemDefinition
- **Import:** `FLExInit.py:15`
- **Note:** Comment says "Fixed: was IWritingSystemDefinition"
- **Usage:** Writing system configuration
- **Status:** Initialized but minimal direct use

### Sldr
- **Import:** `FLExInit.py:16`
- **Usage:** SLDR (Script Library Database Reference) integration
- **Location:** `FLExInit.py`
- **Status:** Initialization only

### SpecialWritingSystemCodes
- **Import:** `FLExProject.py:48`
- **Usage:** Special WS codes (e.g., for audio)
- **Example:** `en-Zxxx-x-audio` for audio content
- **Location:** Used in `AllomorphOperations.py` for audio allomorphs

---

## Casting Operations

### lcm_casting.py Module
- **Location:** `/d/Github/_Projects/_LEX/flexlibs2/flexlibs2/code/lcm_casting.py`
- **Purpose:** Type casting for polymorphic LCM objects
- **Key Function:** `cast_to_concrete()` - convert base interface to concrete type
- **Imports from SIL.LCModel (lines 104-150):**

```python
# MSA types
IMoStemMsa, IMoDerivAffMsa, IMoInflAffMsa, IMoUnclassifiedAffixMsa

# Allomorph types
IMoStemAllomorph, IMoAffixAllomorph, IMoAffixForm

# Phonological rule types
IPhRegularRule, IPhMetathesisRule, IPhReduplicationRule
IPhSimpleContextSeg, IPhSimpleContextNC, IPhSegRuleRHS

# Compound rule types
IMoEndoCompound, IMoExoCompound

# Morphosyntactic prohibition types
(MoAdhocProhibGr, MoAdhocProhibMorph, MoAdhocProhibAllomorph - partially listed)
```

**Usage Pattern:**
```python
from flexlibs2.code.lcm_casting import cast_to_concrete

for msa in entry.MorphoSyntaxAnalysesOC:
    concrete = cast_to_concrete(msa)  # Returns actual type (MoStemMsa, etc.)
```

---

## Object Access Methods in FLExProject

### ObjectFactory()
- **Location:** `FLExProject.py` (inherited from BaseOperations)
- **Usage:** Get factory for creating objects
- **Example:**
  ```python
  factory = project.ObjectFactory(ICmPossibilityListFactory)
  ```

### ObjectRepository()
- **Location:** `FLExProject.py` (inherited from BaseOperations)
- **Usage:** Get repository for querying objects
- **Example:**
  ```python
  repo = project.ObjectRepository(ILexEntryRepository)
  ```

### WSHandle()
- **Location:** `FLExProject.py:1870+`
- **Usage:** Get writing system handle for text operations
- **Example:**
  ```python
  ws_handle = project.WSHandle('en')
  text = TsStringUtils.MakeString(value, ws_handle)
  ```

---

## Known TODOs with Code References

### 1. Linux Flatpak Support
- **File:** `/d/Github/_Projects/_LEX/flexlibs2/flexlibs2/code/FLExGlobals.py`
- **Lines:** 103+ (was 102-105 in original audit)
- **Issue:** FW now uses flatpak on Linux, old path logic doesn't work
- **Current:** Only Windows/macOS supported
- **Status:** Still open since 2025-03-16

### 2. Project Chooser Dialog
- **File:** `/d/Github/_Projects/_LEX/flexlibs2/flexlibs2/code/FLExLCM.py`
- **Line:** 59 (was 53-54 in original audit)
- **Issue:** Using simple file listing instead of FW native dialog
- **Enhancement:** Would use `ChooseLangProjectDialog()` and support network drives
- **Status:** Still open since 2025-03-16

---

## Summary Statistics (refreshed 2026-05-27)

**Total Python Files Scanned:** 106
**Total Files with SIL Imports:** 73
**Total SIL Import Statements:** 569
**Total Unique Classes/Interfaces:** 233
**Distinct SIL Namespaces:** 14

By category (unique class counts):
- **Repositories Imported:** 18 (was 9)
- **Factories Imported:** 74 (was 12)
- **Other Interfaces:** 94
- **Manager/Services:** 2 (IUndoStackManager, IFwMetaDataCacheManaged)
- **Text Interfaces:** 5 (`ITsString`, `ITsStrBldr`, `IMultiString`, `IMultiUnicode`, `FwObjDataTypes`)
- **Exception Types:** 6 (was 5; `StartupException` is new)
- **Tag Classes:** 13 (was 11; `LexEntryRefTags`, `LexRefTypeTags`, `MoMorphTypeTags` are new)
- **Cellar Classes:** 3 (`CellarPropertyType`, `CellarPropertyType as _LCMCellarPropertyType`, `CellarPropertyTypeFilter`)
- **Utility Classes:** 6 (`TsStringUtils`, `ReflectionHelper`, `ThreadHelper`, `LcmFileHelper`, `FwRegistryHelper`, `FwUtils`)
- **UI/Infrastructure:** 10+ (`ProjectId`, `FwLcmUI`, `ChooseLangProjectDialog`, `ProgressDialogWithTask`, `FwDirectoryFinder`, `VersionInfoProvider`, `FwAppArgs`, etc.)
- **Writing System Classes:** 2 (`Sldr`, `WritingSystemDefinition`)
- **Casting/Helper Modules:** 2 (`lcm_casting.py`, `PythonicWrapper.py`)
  -- earlier revisions also listed `CastingOperations.py`, which does not
  and never did exist; corrected under #271. The public casting entry point
  is `from flexicon import cast_to_concrete`.

Top 10 most-used classes (by file count):
1. `ITsString` -- 87 files
2. `TsStringUtils` -- 58 files
3. `ICmPossibility` -- 15 files
4. `ILexEntry` -- 13 files
5. `ILexSense` -- 10 files
6. `ICmPossibilityRepository` -- 7 files
7. `IText` -- 7 files
8. `ICmPossibilityFactory` -- 7 files
9. `ICmObjectRepository` -- 6 files
10. `IDsConstChart` -- 6 files

---

## Cross-Reference: By Domain (refreshed 2026-05-27)

### Grammar Domain (9 Operations classes)
- `Grammar/GramCatOperations.py` - ICmPossibility, ICmPossibilityFactory
- `Grammar/POSOperations.py` - IPartOfSpeechFactory, IPartOfSpeech, ILexEntryRepository
- `Grammar/EnvironmentOperations.py` - IPhEnvironmentFactory, IPhEnvironment, ICmObjectRepository
- `Grammar/PhonemeOperations.py` - IPhPhonemeFactory, IPhCodeFactory
- `Grammar/PhonologicalRuleOperations.py` - Uses casting for polymorphic rules (PhRegularRule, PhMetathesisRule, PhReduplicationRule)
- `Grammar/PhonFeatureOperations.py` - Phonological feature structures
- `Grammar/NaturalClassOperations.py` - IPhNCSegmentsFactory, IPhNCFeaturesFactory
- `Grammar/InflectionFeatureOperations.py` - IFsClosedFeatureFactory, IFsClosedValueFactory, IFsFeatStrucFactory, IFsSymFeatValFactory
- `Grammar/MorphRuleOperations.py` - IMoEndoCompoundFactory, IMoExoCompoundFactory, IMoInflAffixTemplateFactory, IMoInflClassFactory

### Lexicon Domain (10 Operations classes)
- `Lexicon/LexEntryOperations.py` - Core lexical operations, ILexEntryFactory, ILexEntryRefFactory
- `Lexicon/LexSenseOperations.py` - ILexSenseFactory, ILexSenseRepository
- `Lexicon/AllomorphOperations.py` - IMoStemAllomorphFactory, IMoAffixAllomorphFactory
- `Lexicon/MSAOperations.py` - IMoStemMsaFactory, IMoDerivAffMsaFactory, IMoInflAffMsaFactory, IMoUnclassifiedAffixMsaFactory, MsaType, SandboxGenericMSA
- `Lexicon/LexReferenceOperations.py` - ICmPossibilityListFactory, ILexReferenceFactory, ILexRefTypeFactory
- `Lexicon/ExampleOperations.py` - ILexExampleSentenceFactory
- `Lexicon/EtymologyOperations.py` - ILexEtymologyFactory
- `Lexicon/PronunciationOperations.py` - ILexPronunciationFactory
- `Lexicon/SemanticDomainOperations.py` - ICmSemanticDomainFactory
- `Lexicon/VariantOperations.py` - Variant entry refs

### TextsWords Domain (8 Operations classes)
- `TextsWords/TextOperations.py` - ITextRepository, ITextFactory
- `TextsWords/ParagraphOperations.py` - IStTextFactory, IStTxtParaFactory
- `TextsWords/SegmentOperations.py` - ISegmentRepository, ISegmentFactory
- `TextsWords/WordformOperations.py` - IWfiWordformFactory, IWfiWordformRepository
- `TextsWords/WfiAnalysisOperations.py` - IWfiAnalysisFactory, IWfiAnalysisRepository
- `TextsWords/WfiGlossOperations.py` - IWfiGlossFactory, IWfiGlossRepository
- `TextsWords/WfiMorphBundleOperations.py` - IWfiMorphBundleFactory, WfiMorphBundleTags
- `TextsWords/DiscourseOperations.py` - legacy discourse alias

### Notebook Domain (5 Operations classes)
- `Notebook/DataNotebookOperations.py` - IRnGenericRecFactory, IRnResearchNbkRepository
- `Notebook/NoteOperations.py` - Notes / annotation handling
- `Notebook/PersonOperations.py` - ICmPersonFactory, ICmPersonRepository
- `Notebook/LocationOperations.py` - ICmLocationFactory
- `Notebook/AnthropologyOperations.py` - ICmAnthroItemFactory

### Lists Domain (6 Operations classes)
- `Lists/AgentOperations.py` - ICmAgentFactory
- `Lists/PossibilityListOperations.py` - ICmPossibilityListFactory, XmlList, XmlTranslatedLists
- `Lists/PublicationOperations.py` - Publications list
- `Lists/TranslationTypeOperations.py` - ICmTranslationFactory
- `Lists/ConfidenceOperations.py` - Confidence values
- `Lists/OverlayOperations.py` - Overlays

### System Domain (5 Operations classes)
- `System/AnnotationDefOperations.py` - ICmAnnotationDefnFactory, ICmAnnotationDefnRepository
- `System/CheckOperations.py` - Editorial checks
- `System/CustomFieldOperations.py` - Custom field metadata (uses CellarPropertyType heavily)
- `System/ProjectSettingsOperations.py` - Project-wide settings
- `System/WritingSystemOperations.py` - WritingSystemDefinition, Sldr

### Discourse Domain (7 Operations classes)
- `Discourse/ConstChartOperations.py` - IDsConstChartFactory, IDsConstChartRepository, IDsDiscourseFactory, IDsDiscourseDataFactory
- `Discourse/ConstChartRowOperations.py` - IConstChartRowFactory
- `Discourse/ConstChartWordGroupOperations.py` - IConstChartWordGroupFactory
- `Discourse/ConstChartMovedTextOperations.py` - IConstChartMovedTextMarkerFactory
- `Discourse/ConstChartMarkerOperations.py` - Marker access (base)
- `Discourse/ConstChartCellTagOperations.py` - IConstChartTagFactory
- `Discourse/ConstChartClauseMarkerOperations.py` - IConstChartClauseMarkerFactory

### Reversal Domain (2 Operations classes)
- `Reversal/ReversalIndexOperations.py` - IReversalIndexFactory, IReversalIndexRepository
- `Reversal/ReversalIndexEntryOperations.py` - IReversalIndexEntryFactory, ReversalIndexEntryTags

### Scripture Domain (6 Operations classes) -- grown from 2 in original audit
- `Scripture/ScrBookOperations.py` - IScrBookFactory, IScrBookRepository
- `Scripture/ScrDraftOperations.py` - IScrDraftFactory
- `Scripture/ScrSectionOperations.py` - IScrSectionFactory
- `Scripture/ScrTxtParaOperations.py` - IScrTxtParaFactory
- `Scripture/ScrAnnotationsOperations.py` - IScrBookAnnotationsFactory
- `Scripture/ScrNoteOperations.py` - IScrScriptureNoteFactory

### Shared Domain (2 Operations classes + utilities)
- `Shared/FilterOperations.py` - ICmFilterFactory
- `Shared/MediaOperations.py` - ICmMediaFactory, ICmFileFactory, ICmFolderFactory, ICmPictureFactory
- `Shared/string_utils.py`, `Shared/smart_collection.py`, `Shared/wrapper_base.py` - infrastructure (no SIL imports)

---

## How to Use This Reference

1. **Finding where something is imported:**
   - Search this document for the interface/class name
   - Get the file path and line number
   - Use `Read` tool with that path to see context

2. **Understanding usage patterns:**
   - Check "Usage Pattern" sections
   - Look at code examples provided
   - Follow cross-references to see how operations use imports

3. **Checking for missing functionality:**
   - Review "Partially Exposed" and "Not Exposed" sections
   - Check "Known TODOs" for planned improvements
   - Use "Recommendation" sections to decide if something should be wrapped

4. **Adding new Operations classes:**
   - Find similar operation in "Cross-Reference: By Domain"
   - Check what imports it uses
   - Follow the local import pattern from `AllomorphOperations.py` for factories
   - See `lcm_casting.py` for casting examples if dealing with polymorphic types

