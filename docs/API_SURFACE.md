# flexlibs API Surface Documentation

**Version:** 2.4.0
**Generated:** 2026-05-27
**Analysis Tool:** `tools/extract_api_usage.py`

**Last regenerated:** 2026-05-27 via `tools/extract_api_usage.py --all`

## Executive Summary

This document provides a comprehensive analysis of the flexlibs dependency on the SIL FieldWorks LCM (Language and Culture Model) API. Understanding this API surface is critical for:

- **Maintenance**: Tracking which LCM APIs we depend on
- **Compatibility**: Understanding version dependencies
- **Migration Planning**: Identifying areas requiring updates when LCM changes
- **Risk Assessment**: Highlighting critical dependencies used across many files

### Key Metrics

- **Total SIL.* Imports**: 569 import statements
- **Unique Classes Used**: 233 unique LCM classes/interfaces
- **SIL Namespaces Used**: 14 namespaces
- **Files Analyzed**: 73 Python files (with SIL imports) of 106 scanned in `flexicon/code/`
- **Critical Dependencies**: 15 classes used in 5+ files

---

## SIL Namespace Overview

flexlibs depends on 14 SIL namespaces from the FieldWorks LCM API:

| Namespace | Description | Files | Classes | Imports |
|-----------|-------------|-------|---------|---------|
| SIL.LCModel | Core LCModel classes and interfaces | 64 | 203 | 389 |
| SIL.LCModel.Core.KernelInterfaces | Kernel interfaces (ITsString, etc.) | 62 | 5 | 92 |
| SIL.LCModel.Core.Text | Text utilities (TsStringUtils) | 57 | 1 | 58 |
| SIL.FieldWorks.Common.FwUtils | FieldWorks utilities | 4 | 7 | 8 |
| SIL.LCModel.Core.Cellar | Cellar infrastructure | 3 | 3 | 5 |
| SIL.WritingSystems | Writing system definitions | 3 | 2 | 3 |
| SIL.LCModel.Infrastructure | Infrastructure classes | 2 | 2 | 3 |
| SIL.LCModel.Utils | Utility classes | 2 | 2 | 3 |
| SIL.LCModel.Application.ApplicationServices | Application services (XML list import) | 2 | 2 | 2 |
| SIL.LCModel.DomainServices | Domain services (MSA support classes) | 1 | 2 | 2 |
| SIL.FieldWorks | FieldWorks core | 1 | 1 | 1 |
| SIL.FieldWorks.Common.Controls | UI controls | 1 | 1 | 1 |
| SIL.FieldWorks.FdoUi | FDO UI components | 1 | 1 | 1 |
| SIL.FieldWorks.FwCoreDlgs | Core dialogs | 1 | 1 | 1 |

---

## Critical Dependencies (5+ Files)

These classes are used in 5 or more files and represent critical dependencies:

| Class | Usage Count | Type | Description |
|-------|-------------|------|-------------|
| **ITsString** | 87 | Interface | Multilingual string interface (CRITICAL) |
| **TsStringUtils** | 58 | Utility | Text string manipulation utilities (CRITICAL) |
| ICmPossibility | 15 | Interface | Possibility list items |
| ILexEntry | 13 | Interface | Lexical entry interface |
| ILexSense | 10 | Interface | Lexical sense interface |
| IText | 7 | Interface | Text interface |
| ICmPossibilityRepository | 7 | Repository | Accesses possibility items |
| ICmPossibilityFactory | 7 | Factory | Creates possibility items |
| ICmObjectRepository | 6 | Repository | Accesses CmObjects by HVO |
| IDsConstChart | 6 | Interface | Discourse chart interface |
| IStTxtParaFactory | 6 | Factory | Creates text paragraphs |
| IStTxtPara | 5 | Interface | Structured text paragraph |
| IConstChartRow | 5 | Interface | Chart row |
| ICmPossibilityListFactory | 5 | Factory | Creates possibility lists |
| IStTextFactory | 5 | Factory | Creates structured text |

**Note**: ITsString and TsStringUtils are used virtually everywhere and represent the most critical dependencies.

---

## API Surface by Category

### 1. Repositories (Data Access)

Repositories provide read-only access to collections of objects.

**Total Repositories Used**: 18

| Repository | Usage | Namespace |
|------------|-------|-----------|
| ICmPossibilityRepository | 7 | SIL.LCModel |
| ICmObjectRepository | 6 | SIL.LCModel |
| ILexEntryRepository | 3 | SIL.LCModel |
| IWfiAnalysisRepository | 3 | SIL.LCModel |
| ITextRepository | 3 | SIL.LCModel |
| IWfiWordformRepository | 2 | SIL.LCModel |
| ILexRefTypeRepository | 2 | SIL.LCModel |
| ISegmentRepository | 1 | SIL.LCModel |
| IDsConstChartRepository | 1 | SIL.LCModel |
| ILexSenseRepository | 1 | SIL.LCModel |
| ILexEntryTypeRepository | 1 | SIL.LCModel |
| IWfiGlossRepository | 1 | SIL.LCModel |
| IStTxtParaRepository | 1 | SIL.LCModel |
| IRnResearchNbkRepository | 1 | SIL.LCModel |
| ICmPersonRepository | 1 | SIL.LCModel |
| IReversalIndexRepository | 1 | SIL.LCModel |
| IScrBookRepository | 1 | SIL.LCModel |
| ICmAnnotationDefnRepository | 1 | SIL.LCModel |

### 2. Factories (Object Creation)

Factories create new instances of LCM objects.

**Total Factories Used**: 74

#### High-Usage Factories (3+ uses):
| Factory | Usage | Purpose |
|---------|-------|---------|
| ICmPossibilityFactory | 7 | Create possibility list items |
| IStTxtParaFactory | 6 | Create text paragraphs |
| ICmPossibilityListFactory | 5 | Create possibility lists |
| IStTextFactory | 5 | Create structured text objects |
| ICmFileFactory | 4 | Create file objects |
| ILexEntryRefFactory | 3 | Create entry references |
| IMoStemAllomorphFactory | 3 | Create stem allomorphs |
| IMoAffixAllomorphFactory | 3 | Create affix allomorphs |
| IWfiGlossFactory | 3 | Create wordform glosses |
| IWfiMorphBundleFactory | 3 | Create morph bundles |

#### Mid-Usage Factories (2 uses):
- ICmFolderFactory
- ICmTranslationFactory
- IDsConstChartFactory
- IFsFeatStrucFactory
- ILexEtymologyFactory
- ILexExampleSentenceFactory
- ILexPronunciationFactory
- ILexSenseFactory
- IMoInflAffMsaFactory
- IMoStemMsaFactory
- IPhRegularRuleFactory
- IScrBookAnnotationsFactory
- IScrScriptureNoteFactory
- IWfiAnalysisFactory

#### Other Factories (alphabetical):
- ICmAgentFactory
- ICmAnnotationDefnFactory
- ICmAnthroItemFactory
- ICmBaseAnnotationFactory
- ICmFilterFactory
- ICmLocationFactory
- ICmMediaFactory
- ICmPersonFactory
- ICmPictureFactory
- ICmSemanticDomainFactory
- IConstChartClauseMarkerFactory
- IConstChartMovedTextMarkerFactory
- IConstChartRowFactory
- IConstChartTagFactory
- IConstChartWordGroupFactory
- IDsDiscourseDataFactory
- IDsDiscourseFactory
- IFsClosedFeatureFactory
- IFsClosedValueFactory
- IFsSymFeatValFactory
- ILexEntryFactory
- ILexReferenceFactory
- ILexRefTypeFactory
- IMoDerivAffMsaFactory
- IMoEndoCompoundFactory
- IMoExoCompoundFactory
- IMoInflAffixTemplateFactory
- IMoInflClassFactory
- IMoUnclassifiedAffixMsaFactory
- IPartOfSpeechFactory
- IPhCodeFactory
- IPhEnvironmentFactory
- IPhMetathesisRuleFactory
- IPhNCFeaturesFactory
- IPhNCSegmentsFactory
- IPhPhonemeFactory
- IPhReduplicationRuleFactory
- IPhSegRuleRHSFactory
- IPhSimpleContextNCFactory
- IPhSimpleContextSegFactory
- IReversalIndexEntryFactory
- IReversalIndexFactory
- IRnGenericRecFactory
- IScrBookFactory
- IScrDraftFactory
- IScrSectionFactory
- IScrTxtParaFactory
- ISegmentFactory
- ITextFactory
- IWfiWordformFactory

### 3. Interfaces (Data Objects)

These interfaces represent the core data model objects.

**Total Interfaces Used**: 94

#### Core Lexicon Interfaces (High Usage):
| Interface | Usage | Description |
|-----------|-------|-------------|
| ILexEntry | 13 | Lexical entry |
| ILexSense | 10 | Sense of lexical entry |
| ILexExampleSentence | 2 | Example sentence |
| ILexEntryRef | 2 | Lexical entry reference (variant, complex form) |
| ILexEtymology | 1 | Etymology information |
| ILexPronunciation | 1 | Pronunciation |
| ILexReference | 1 | Lexical reference (relation) |
| ILexRefType | 1 | Type of lexical reference |
| ILexEntryType | 1 | Type of lexical entry |
| IVariantComponentLexeme | 1 | Variant component |

#### Core Wordform/Analysis Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| IWfiAnalysis | 4 | Wordform analysis |
| IWfiWordform | 4 | Wordform |
| IWfiGloss | 1 | Wordform gloss |
| IWfiMorphBundle | 1 | Morpheme bundle |
| IAnalysis | 1 | Analysis |

#### Core Text Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| IText | 7 | Text object |
| IStTxtPara | 5 | Structured text paragraph |
| IStText | 2 | Structured text |
| ISegment | 2 | Text segment |

#### Possibility List Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| ICmPossibility | 15 | Generic possibility item |
| ICmPossibilityList | 4 | List of possibilities |
| ICmSemanticDomain | 3 | Semantic domain |

#### Discourse Chart Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| IDsConstChart | 6 | Discourse constituent chart |
| IConstChartRow | 5 | Chart row |
| IConstChartWordGroup | 4 | Word group in chart |
| IConstChartTag | 1 | Chart tag |
| IConstChartClauseMarker | 1 | Clause marker |
| IConstChartMovedTextMarker | 1 | Moved text marker |
| IDsDiscourse | 1 | Discourse data root |
| IDsDiscourseData | 1 | Discourse data object |

#### Morphology Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| IMoMorphType | 3 | Morpheme type |
| IMoForm | 3 | Morphological form |
| IMoInflClass | 2 | Inflection class |
| IMoEndoCompound | 1 | Endocentric compound rule |
| IMoExoCompound | 1 | Exocentric compound rule |
| IMoInflAffixTemplate | 1 | Inflectional affix template |
| IMoAdhocProhibGr | 1 | Ad-hoc co-occurrence prohibition group |
| IMoAdhocProhibMorph | 1 | Morpheme-level co-occurrence prohibition |
| IMoAdhocProhibAllomorph | 1 | Allomorph-level co-occurrence prohibition |
| IMoMorphSynAnalysis | 1 | Morph-syntactic analysis |
| IMoStemMsa | 1 | Stem MSA |
| IMoDerivAffMsa | 1 | Derivational affix MSA |
| IMoInflAffMsa | 1 | Inflectional affix MSA |
| IMoUnclassifiedAffixMsa | 1 | Unclassified affix MSA |

#### Grammar/Phonology Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| IFsFeatStruc | 3 | Feature structure |
| IFsClosedFeature | 3 | Closed feature |
| IPhEnvironment | 2 | Phonological environment |
| IPhPhoneme | 2 | Phoneme |
| IFsClosedValue | 2 | Closed feature value |
| IPartOfSpeech | 2 | Part of speech |
| IPhNaturalClass | 1 | Natural class |
| IPhNCSegments | 1 | Natural class segments |
| IPhNCFeatures | 1 | Natural class features |
| IPhCode | 1 | Phonological code |
| IPhRegularRule | 1 | Regular phonological rule |
| IPhMetathesisRule | 1 | Metathesis rule |
| IPhReduplicationRule | 1 | Reduplication rule |
| IPhSimpleContextSeg | 1 | Simple segment context |
| IPhSimpleContextNC | 1 | Simple natural-class context |
| IPhSegRuleRHS | 1 | Segment rule right-hand side |
| IFsFeatDefn | 1 | Feature definition |
| IFsSymFeatVal | 1 | Symbolic feature value |

#### Scripture Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| IScrBook | 4 | Scripture book |
| IScrScriptureNote | 3 | Scripture note |
| IScrSection | 3 | Scripture section |
| IScrTxtPara | 3 | Scripture text paragraph |
| IScripture | 2 | Scripture |
| IScrBookAnnotations | 2 | Book annotations |
| IScrDraft | 1 | Scripture draft |

#### Notebook/Anthropology Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| ICmPerson | 4 | Person |
| ICmLocation | 2 | Location |
| IRnGenericRec | 2 | Generic notebook record |
| ICmAnthroItem | 2 | Anthropology item |

#### Reversal Index Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| IReversalIndex | 3 | Reversal index |
| IReversalIndexEntry | 3 | Reversal index entry |

#### Other Data Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| ICmAnnotationDefn | 2 | Annotation definition |
| ICmAgent | 2 | Agent |
| ICmAgentEvaluation | 2 | Agent evaluation |
| ICmFile | 3 | File object |
| ICmMedia | 1 | Media object |
| ICmPicture | 1 | Picture |
| ICmFilter | 1 | Filter |
| ICmFolder | 1 | Folder |
| ICmTranslation | 1 | Translation |
| ICmBaseAnnotation | 1 | Base annotation |
| IStStyle | 1 | Style |

#### Special Interfaces:
| Interface | Usage | Description |
|-----------|-------|-------------|
| ILangProject | 3 | The root project object |
| IUndoStackManager | 1 | Undo/redo management |
| IFwMetaDataCacheManaged | 2 | Metadata cache (SIL.LCModel.Infrastructure) |
| IDataReader | 1 | Data reader (SIL.LCModel.Infrastructure) |

### 4. Tags Classes (Field IDs)

Tags provide integer constants for accessing object fields.

**Total Tags Used**: 13

| Tags Class | Usage | Description |
|------------|-------|-------------|
| LexEntryTags | 3 | Field IDs for LexEntry |
| MoMorphTypeTags | 3 | Field IDs for morph types |
| LexSenseTags | 2 | Field IDs for LexSense |
| LexExampleSentenceTags | 2 | Field IDs for example sentences |
| MoFormTags | 2 | Field IDs for MoForm |
| WfiWordformTags | 1 | Field IDs for wordforms |
| WfiGlossTags | 1 | Field IDs for glosses |
| WfiAnalysisTags | 1 | Field IDs for analyses |
| WfiMorphBundleTags | 1 | Field IDs for morph bundles |
| TextTags | 1 | Field IDs for Text |
| ReversalIndexEntryTags | 1 | Field IDs for reversal entries |
| LexEntryRefTags | 1 | Field IDs for entry refs |
| LexRefTypeTags | 1 | Field IDs for ref types |

### 5. Utility Classes

#### Text/String Utilities (CRITICAL):
| Utility | Usage | Namespace | Description |
|---------|-------|-----------|-------------|
| **TsStringUtils** | 58 | SIL.LCModel.Core.Text | String manipulation (CRITICAL) |
| **ITsString** | 87 | SIL.LCModel.Core.KernelInterfaces | Multilingual string (CRITICAL) |
| ITsStrBldr | 2 | SIL.LCModel.Core.KernelInterfaces | String builder |

#### Multi-String Interfaces:
| Utility | Usage | Namespace | Description |
|---------|-------|-----------|-------------|
| IMultiUnicode | 1 | SIL.LCModel.Core.KernelInterfaces | Multi-Unicode string |
| IMultiString | 1 | SIL.LCModel.Core.KernelInterfaces | Multi-string |

#### Reflection/Metadata:
| Utility | Usage | Namespace | Description |
|---------|-------|-----------|-------------|
| ReflectionHelper | 2 | SIL.LCModel.Utils | Reflection utilities |
| IFwMetaDataCacheManaged | 2 | SIL.LCModel.Infrastructure | Metadata cache |
| IDataReader | 1 | SIL.LCModel.Infrastructure | Data reader |

#### Writing Systems:
| Utility | Usage | Namespace | Description |
|---------|-------|-----------|-------------|
| WritingSystemDefinition | 2 | SIL.WritingSystems | Writing system |
| SpecialWritingSystemCodes | 2 | SIL.LCModel | Special WS codes |
| Sldr | 1 | SIL.WritingSystems | SLDR (writing systems) |

#### FieldWorks Utilities:
| Utility | Usage | Namespace | Description |
|---------|-------|-----------|-------------|
| FwUtils | 2 | SIL.FieldWorks.Common.FwUtils | General FW utilities |
| FwDirectoryFinder | 1 | SIL.FieldWorks.Common.FwUtils | Directory locator |
| FwRegistryHelper | 1 | SIL.FieldWorks.Common.FwUtils | Registry access |
| ThreadHelper | 1 | SIL.FieldWorks.Common.FwUtils | Threading utilities |
| FwAppArgs | 1 | SIL.FieldWorks.Common.FwUtils | Application arguments |
| VersionInfoProvider | 1 | SIL.FieldWorks.Common.FwUtils | Version information |

### 6. Core Infrastructure Classes

| Class | Usage | Namespace | Description |
|-------|-------|-----------|-------------|
| LcmCache | 1 | SIL.LCModel | The main cache object |
| LcmSettings | 1 | SIL.LCModel | LCM settings |
| LcmFileHelper | 1 | SIL.LCModel | File operations |
| CellarPropertyType | 2 | SIL.LCModel.Core.Cellar | Property type enum |
| CellarPropertyTypeFilter | 2 | SIL.LCModel.Core.Cellar | Property filtering |
| FwObjDataTypes | 1 | SIL.LCModel.Core.KernelInterfaces | Object data types |

### 7. Application & Domain Services (New in 2.4.x)

| Class | Usage | Namespace | Description |
|-------|-------|-----------|-------------|
| XmlTranslatedLists | 1 | SIL.LCModel.Application.ApplicationServices | Translated XML list import |
| XmlList | 1 | SIL.LCModel.Application.ApplicationServices | XML list import support |
| SandboxGenericMSA | 1 | SIL.LCModel.DomainServices | Sandbox generic MSA (used by MSAOperations) |
| MsaType | 1 | SIL.LCModel.DomainServices | MSA type enumeration |

### 8. UI Components (Used in FLExProject.py, FLExLCM.py)

| Class | Usage | Namespace | Description |
|-------|-------|-----------|-------------|
| ProgressDialogWithTask | 1 | SIL.FieldWorks.Common.Controls | Progress dialog |
| FwLcmUI | 1 | SIL.FieldWorks.FdoUi | LCM UI |
| ChooseLangProjectDialog | 1 | SIL.FieldWorks.FwCoreDlgs | Project chooser |
| ProjectId | 1 | SIL.FieldWorks | Project identifier |

### 9. Exception Classes

| Exception | Usage | Namespace | Description |
|-----------|-------|-----------|-------------|
| LcmInvalidClassException | 1 | SIL.LCModel | Invalid class error |
| LcmInvalidFieldException | 1 | SIL.LCModel | Invalid field error |
| LcmFileLockedException | 1 | SIL.LCModel | File locked error |
| LcmDataMigrationForbiddenException | 1 | SIL.LCModel | Migration forbidden |
| WorkerThreadException | 1 | SIL.LCModel.Utils | Worker thread error |
| StartupException | 1 | SIL.FieldWorks.Common.FwUtils | Startup error |

### 10. Other Classes

| Class | Usage | Namespace | Description |
|-------|-------|-----------|-------------|
| GenDate | 1 | SIL.LCModel | Generic date |
| Opinions | 1 | SIL.LCModel | Agent-evaluation opinion enum |

---

## Namespace Dependency Details

### SIL.LCModel (Core)

**Files**: 64 | **Classes**: 203 | **Imports**: 389

This is the primary namespace containing all LCM data model interfaces, repositories, and factories.

**Key Dependencies**:
- All Repository interfaces
- All Factory interfaces
- All data object interfaces (ILexEntry, IWfiWordform, etc.)
- All Tags classes
- Core exceptions and enums

**Risk Level**: **HIGH** - This is the core dependency. Changes to LCM interfaces directly impact flexicon.

### SIL.LCModel.Core.KernelInterfaces

**Files**: 62 | **Classes**: 5 | **Imports**: 92

**Critical Classes**:
- ITsString (87 uses) - Multilingual string representation
- ITsStrBldr (2 uses) - String builder
- IMultiUnicode, IMultiString - Multi-language string interfaces
- FwObjDataTypes - Object data type enumeration

**Risk Level**: **CRITICAL** - ITsString is used everywhere. Any changes to this interface would require massive refactoring.

### SIL.LCModel.Core.Text

**Files**: 57 | **Classes**: 1 | **Imports**: 58

**Critical Classes**:
- TsStringUtils (58 uses) - Static utility methods for string manipulation

**Risk Level**: **CRITICAL** - Used in almost every file for string operations.

### SIL.LCModel.Core.Cellar

**Files**: 3 | **Classes**: 3 | **Imports**: 5

**Classes**:
- CellarPropertyType - Property type enumeration
- CellarPropertyTypeFilter - Property filtering
- CellarPropertyType (aliased as _LCMCellarPropertyType)

**Risk Level**: **LOW** - Used only in a handful of files (FLExProject.py, CustomFieldOperations.py, and one more).

### SIL.LCModel.Infrastructure

**Files**: 2 | **Classes**: 2 | **Imports**: 3

**Classes**:
- IFwMetaDataCacheManaged - Metadata cache access
- IDataReader - Data reading interface

**Risk Level**: **LOW** - Limited usage in advanced scenarios.

### SIL.LCModel.Utils

**Files**: 2 | **Classes**: 2 | **Imports**: 3

**Classes**:
- ReflectionHelper - Reflection utilities
- WorkerThreadException - Exception type

**Risk Level**: **LOW** - Utility functions, minimal impact.

### SIL.LCModel.Application.ApplicationServices

**Files**: 2 | **Classes**: 2 | **Imports**: 2

**Classes**:
- XmlList - XML list import support
- XmlTranslatedLists - Translated XML list import

**Risk Level**: **LOW** - New in 2.4.x; used by list import paths.

### SIL.LCModel.DomainServices

**Files**: 1 | **Classes**: 2 | **Imports**: 2

**Classes**:
- SandboxGenericMSA - Generic MSA used by MSAOperations
- MsaType - MSA type enumeration

**Risk Level**: **LOW** - New in 2.4.x; isolated to MSA-related code.

### SIL.FieldWorks.* (4 namespaces)

**Files**: 4 (mainly FLExProject.py, FLExLCM.py, FLExInit.py)
**Total Classes**: 10
**Total Imports**: 11

These provide FieldWorks-specific utilities, UI components, and initialization support.

**Risk Level**: **MEDIUM** - Used for project initialization and UI. Changes could affect startup.

### SIL.WritingSystems

**Files**: 3 | **Classes**: 2 | **Imports**: 3

**Classes**:
- WritingSystemDefinition - Writing system representation
- Sldr - SLDR (SIL Locale Data Repository) access

**Risk Level**: **LOW** - Used for writing system operations.

---

## Dependency Impact Analysis

### Files with Highest API Dependencies

Top 10 files with the most SIL.* imports:

1. **FLExProject.py** - 50 imports (Core infrastructure file)
2. **lcm_casting.py** - 27 imports (Casting utilities, new architecture layer)
3. **Lexicon/LexSenseOperations.py** - 27 imports (Core lexicon)
4. **Lexicon/LexEntryOperations.py** - 18 imports (Core lexicon)
5. **System/CustomFieldOperations.py** - 15 imports (Complex custom fields)
6. **Lexicon/LexReferenceOperations.py** - 13 imports (Lexical relations)
7. **Scripture/ScrNoteOperations.py** - 13 imports (Scripture notes)
8. **Lexicon/MSAOperations.py** - 12 imports (Morphosyntactic analyses)
9. **TextsWords/TextOperations.py** - 12 imports (Text management)
10. **TextsWords/WfiAnalysisOperations.py** - 12 imports (Wordform analysis)

### API Usage by Module Area

| Module Area | Files | Total Imports | Avg Imports/File |
|-------------|-------|---------------|------------------|
| Lexicon | 11 | 123 | 11.2 |
| Top-level (FLExProject, lcm_casting, FLExLCM, etc.) | 6 | 94 | 15.7 |
| Grammar | 12 | 61 | 5.1 |
| TextsWords | 8 | 59 | 7.4 |
| Scripture | 6 | 45 | 7.5 |
| Notebook | 6 | 43 | 7.2 |
| Discourse | 7 | 40 | 5.7 |
| System | 5 | 40 | 8.0 |
| Lists | 7 | 33 | 4.7 |
| Shared | 3 | 19 | 6.3 |
| Reversal | 2 | 12 | 6.0 |

---

## Migration and Compatibility Considerations

### High-Risk Areas for LCM Changes

1. **ITsString / TsStringUtils** - Used in 87/58 files respectively
   - Any API changes here would require extensive refactoring
   - Consider creating wrapper/adapter layer

2. **Repository Interfaces** - Used throughout for data access
   - Changes to query methods would impact many files
   - Maintain backward compatibility where possible

3. **Factory Interfaces** - 74 distinct factories used for object creation
   - Changes to factory methods affect object creation patterns
   - May need factory adapters for version compatibility

4. **Casting Architecture (`code/lcm_casting.py`)** - 27 imports
   - Internal-only module that hides interface/casting complexity from callers
   - Changes to LCM concrete-vs-base interface hierarchies propagate here first

### Recommended Mitigation Strategies

1. **Create Abstraction Layer**
   - Wrap critical dependencies (ITsString, TsStringUtils) in flexlibs helpers
   - Isolate LCM-specific code to minimize surface area

2. **Version Compatibility Testing**
   - Test against multiple FLEx/LCM versions
   - Document compatible version ranges

3. **Dependency Monitoring**
   - Regularly run `extract_api_usage.py` to track changes
   - Monitor for new dependencies or increased usage

4. **API Stability Tracking**
   - Track which LCM APIs are stable vs. experimental
   - Prefer stable APIs when alternatives exist

---

## Appendix: Complete Class List

See `api_usage_summary.json` for the complete list of all 233 classes used.

To regenerate this data:
```bash
python tools/extract_api_usage.py --all --code-dir flexicon/code
```

The tool defaults to `../flexlibs/code` (the legacy path); pass `--code-dir flexicon/code` (or an absolute path) to point it at the current source tree.

---

**Document Maintained By**: Programmer Team 1
**Last Updated**: 2026-05-27
**Tool**: `tools/extract_api_usage.py`
