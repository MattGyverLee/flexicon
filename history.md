# flexicon History

> Formerly `flexlibs2`. This file is the project's own development history --
> it is no longer an upstream-sync mirror of cdfarrow/flexlibs, which flexicon
> no longer tracks. See `CHANGELOG.md` for the released-version changelog.

## Known Issues

None

## History

### 2026-06-24 to 2026-06-30 — v4.0.1 patch: null-guards, cast-on-yield fixes, test hygiene

**`LexEntryOperations.GetComplexFormsNotSubentries` null-guard** (`66b8eb3`)

None-guarded the `sense.OwnerOfClass(LexEntryTags.kClassId)` cast to
`ILexEntry`. Unconditional cast raised `TypeError` when `OwnerOfClass`
returns `None`; now returns empty result, mirroring the safer pattern at
line 2789.

Also regenerated the LCM contract baseline snapshot to admit the
`IMoStratum`/`IMoStratumFactory` dependencies introduced by
`StratumOperations` (672f292); the previous baseline predated that module
and failed `test_no_new_type_dependencies`.

**Grammar live-test self-restore refactor** (`ddbfe3c`)

18 phon-feature, natural-class, and phon-rule live tests restructured as
self-restoring round-trips. Removed pre-clean calls (crash surface +
failure-masking); each test now follows create -> assert -> delete ->
assert-gone. Verified: two consecutive runs with no DB restore both
returned 33 passed / 1 skipped.

**Category 5 cast-on-yield sweep (closes Category 5)** (`92762fa`)

- `SemanticDomainOperations.GetSubdomains`: yield `ICmSemanticDomain`
- `LocationOperations.GetSublocations`: yield `ICmLocation`
- `InflectionFeatureOperations.InflectionClassGetAll`: yield `IMoInflClass`

All three previously yielded raw base-interface objects.

Added `ProjectSettingsOperations` LCM-backed accessors: `GetProjectGuid`,
`GetProjectDescription`, `GetExternalLink`, `GetAnalysisWritingSystem`,
`GetVernacularWritingSystem`. `GetProjectStatus` omitted — no LCM backing.

**Reversal NRE null-guard (Category 7)** (`fd156ee`)

`ReversalIndexEntryOperations.__GetEntryWS` now raises `FP_ParameterError`
(naming `entry.Hvo`) when `entry.ReversalIndex` is `None`, replacing the
`NullReferenceException` that surfaced during cleanup of orphaned entries.

WS getters in `ProjectSettingsOperations` return `None` when `project.lp`
is unavailable (defensive follow-up to the accessors added in `92762fa`).

**API Issues doc updates** (`a1d4bb3`, `57ed7a0`)

Category 5 marked RESOLVED; Category 4 ProjectSettings table updated;
Category 7 reversal entry updated; Category 3 latent-gap notes added.

---

### 2026-05-30 — /lex-lead cycle: Pattern A sweep + Category 8 doc fix + #172 BaselineText partial

**Pattern A sweep — typed Owner casts (closes #166, #168, #159)** (`295f613`)

14 raw `Owner` return sites across 10 files converted to properly typed casts
(`ILexEntry(obj.Owner)`, `ILexSense(obj.Owner)`, etc.):

- ExampleOperations.py, VariantOperations.py, PronunciationOperations.py,
  LexReferenceOperations.py, LexSenseOperations.py, WfiAnalysisOperations.py,
  WfiGlossOperations.py, WfiMorphBundleOperations.py, SegmentOperations.py,
  ParagraphOperations.py

Closes:
- #166 HIGH — silent orphan in ExampleOperations.Duplicate (untyped Owner used
  as parent reference, object created with wrong parent relationship)
- #168 MEDIUM — 7 GetOwning*/GetParent* methods returning raw Owner across
  Lexicon and TextsWords modules
- #159 MEDIUM — Segment/Paragraph Duplicate/Split/Merge raw Owner

Verification: 94 tests passing; all in-scope sites converted; out-of-scope
siblings preserved. QC: 88/100 PASS-WITH-NOTES.

**Category 8 API docs corrected (closes #173)** (`3bbbcd9`)

`docs/API_ISSUES_CATEGORIZED.md` Category 8 (same-name fields with different LCM
types):
- Corrected the `Source` field row: field lives on `IStText`, not
  `ICmBaseAnnotation` (verified from liblcm `InterfaceAdditions.cs:3018`).
  Stale `ICmBaseAnnotation.Source` comments remain in BaseOperations.py:1872 and
  LexSenseOperations.py:599 — flagged for follow-up.
- Added new row for `ISegment.BaselineText`: `ITsString` single-WS read-only
  computed property; backed by `IStTxtPara.Contents`; `AnalysisAdjuster`
  re-derives segments via `ContentsSideEffects`.

**#172 BaselineText read/write — 2/7 sites fixed** (`20e4a0d`, `14f8840`, `de5a173`)

SegmentOperations.py:
- `SetBaselineText` corrected to the proper write idiom: build via
  `para.Contents.GetBldr().ReplaceTsString(begin, end, new_run)`, then assign
  `para.Contents = bldr.GetString()` — fires `ContentsSideEffects` →
  `AnalysisAdjuster.AdjustAnalysis`.
- `GetSyncableProperties` BaselineText read fixed (was calling
  `GetMultiStringDict` on an `ITsString`, which is wrong type); now uses
  `bt.get_Properties(0).GetIntPropValues(1, 0)[0]` to extract WS handle
  (live-verified on Sena 3, returns e.g. 999000003).
- `None` guard added in `SetBaselineText`; `DeprecationWarning` silenced in
  three internal callers.
- 7 new tests (`TestGetSyncablePropertiesBaselineText`) added.

Regression fix (`14f8840`): initial replacement used `bt.get_WritingSystem(0)`
(does not exist on `ITsString`); corrected to verified idiom above.

5 entangled sites (Create, Duplicate, SplitSegment, MergeSegments,
RebuildSegments) deferred with `TODO(#174)` annotations — these methods manually
mutate `SegmentsOS` and require architectural rework per `AnalysisAdjuster`
contract. **#172 is NOT closed.**

**New issue filed: #174** — Segment Create/SplitSegment/MergeSegments/
RebuildSegments/Duplicate: replace manual `SegmentsOS` mutation with
`IStTxtPara.Contents` edits.

---

### 2.3.0 - 28 Feb 2026

**Extended Domain Coverage Release**

This release extends wrapper classes and smart collections to additional FLEx domains, completing the unified object-oriented API.

**New Features:**

+ **5 New Wrapper Classes** with type-safe operations:
    + Allomorph (allomorph forms and variants)
    + CompoundRule (compound rule definitions)
    + AdhocProhibition (morphosyntactic prohibitions)
    + Annotation (project annotations and notes)
    + AffixTemplate (morpheme slot templates)

+ **Type-Safe Collections** for unified filtering:
    + AllomorphCollection, CompoundRuleCollection, ProhibitionCollection, AnnotationCollection, AffixTemplateCollection
    + All collections support smart type breakdown on display

+ **Python Type Hints** across all wrapper properties for IDE support and code clarity

+ **Documentation**: Usage guides for each new domain in `/docs/USAGE_*.md`

**Backward Compatibility:**

100% maintained. All v2.0 and v2.1 APIs unchanged.

### 2.2.0 - Feb 2026

**Wrapper Classes and Smart Collections Release**

This release introduces a unified object-oriented API that hides the complexity of the two-layer LCM type system (base interfaces + concrete types).

**New Features:**

+ **Wrapper Classes** that transparently handle type casting:
    + PhonologicalRule (PhRegularRule, PhMetathesisRule, PhReduplicationRule)
    + MorphosyntacticAnalysis (MoStemMsa, MoInflAffMsa, etc.)
    + PhonologicalContext (PhIterContextual, PhSimpleContext, etc.)

+ **Smart Collections** with type-aware display and filtering:
    + RuleCollection, MSACollection, ContextCollection
    + Display shows type breakdown: "12 rules (PhRegularRule: 7, PhMetathesisRule: 3, PhReduplicationRule: 2)"
    + Unified filtering across all concrete types

+ **Type Safety**: Internal casting architecture validates merge operations and deep clones

+ **Backward Compatibility**: 100% maintained with v2.0

### 2.1.0 - Nov 2025

**Stability and Testing Release**

This release focused on comprehensive testing, bug fixes, and operational improvements.

**Improvements:**

+ Comprehensive test suite covering all 44 Operations classes
+ Bug fixes for ITsString handling in multilingual fields
+ Improved error messages for common user mistakes
+ Extended documentation with usage examples

**Backward Compatibility:**

100% maintained with v2.0.

### 2.0.0 - 24 Nov 2025

**Major Release: Comprehensive CRUD Operations**

This release introduces a complete set of Operations classes providing intuitive, object-oriented access to all major FLEx data types. The new API significantly expands flexlibs capabilities while maintaining full backward compatibility with v1.x code.

**New Features:**

+ **44 Operations Classes** providing 793+ methods organized into 6 topic areas:
    + **Grammar** (8 classes): POSOperations, PhonemeOperations, GramCatOperations, NaturalClassOperations, EnvironmentOperations, PhonologicalRuleOperations, MorphRuleOperations, InflectionFeatureOperations
    + **Lexicon** (10 classes): LexEntryOperations, LexSenseOperations, ExampleOperations, PronunciationOperations, VariantOperations, AllomorphOperations, EtymologyOperations, LexReferenceOperations, ReversalOperations, SemanticDomainOperations
    + **Texts & Words** (10 classes): TextOperations, ParagraphOperations, SegmentOperations, WordformOperations, WfiAnalysisOperations, WfiGlossOperations, WfiMorphBundleOperations, MediaOperations, FilterOperations, DiscourseOperations
    + **Notebook** (5 classes): DataNotebookOperations, NoteOperations, PersonOperations, LocationOperations, AnthropologyOperations
    + **Lists** (6 classes): PossibilityListOperations, PublicationOperations, TranslationTypeOperations, OverlayOperations, ConfidenceOperations, AgentOperations
    + **System** (5 classes): WritingSystemOperations, CustomFieldOperations, ProjectSettingsOperations, AnnotationDefOperations, CheckOperations

+ **Organized Code Structure**: Operations files organized into topic folders matching FLEx's architecture:
    + `flexlibs/code/Grammar/`
    + `flexlibs/code/Lexicon/`
    + `flexlibs/code/TextsWords/`
    + `flexlibs/code/Notebook/`
    + `flexlibs/code/Lists/`
    + `flexlibs/code/System/`

+ **CRUD Operations**: Each Operations class provides comprehensive Create, Read, Update, and Delete methods for its data type

+ **Lazy Loading**: Operations classes are instantiated only when accessed via FLExProject properties (e.g., `project.POS`, `project.LexEntry`, `project.Texts`)

+ **Full Backward Compatibility**: All v1.x API methods remain available and unchanged. Existing code will continue to work without modification.

**Example Usage:**

```python
import flexlibs2

flexlibs2.FLExInitialize()
project = flexlibs2.FLExProject()
project.OpenProject('MyProject', writeEnabled=True)

# Create a lexical entry with the new API
entry = project.LexEntry.Create("run", "stem")
sense = project.LexEntry.AddSense(entry, "to move rapidly on foot")
project.Senses.SetGloss(sense, "run", "en")

# Old v1.x API still works
allEntries = project.LexiconAllEntries()

project.CloseProject()
flexlibs2.FLExCleanup()
```

**Breaking Changes:**

None. This release maintains 100% backward compatibility with v1.x.

### 1.2.8 - 10 Sep 2025

+ FLExProject functions:
    + Added LexiconClearListFieldSingle() 
    + Added LexiconSetLexemeForm()
    + Added LexiconGetExampleCustomFields()
    + Added LexiconGetAllomorphCustomFields()

### 1.2.7 - 25 Aug 2025

+ Supports Python 3.8 - 3.13
+ Supports FieldWorks 9.0.17 - 9.3.1

+ FLExProject functions:
    + Added GetFieldID()
    + Added support for Lists (single or multiple) in GetCustomFieldValue()
    + Added ListFieldPossibilityList()
    + Added ListFieldPossibilities()
    + Added ListFieldLookup()
    + Added LexiconSetListFieldSingle() 
    + Added LexiconSetListFieldMultiple() 

### 1.2.6 - 26 Jun 2025

+ Supports Python 3.8 - 3.13
+ Supports FieldWorks 9.0.17 - 9.2.8

### 1.2.5 - 13 Jun 2025

+ When generating the list of projects, check that the fwdata file 
  exists, not just the directory. [Issue #14]
+ New function:
    + OpenProjectInFW(projectName)
+ Tidied up the presentation of the API documentation.

### 1.2.4 - 14 Aug 2024

+ New FLExProject function:
    + ObjectRepository(repository)

### 1.2.3 - 9 Jul 2024

+ GetAllSemanticDomains() returns ICmSemanticDomain objects
+ New FLExProject functions:
    + Object(hvoOrGuid)
    + LexiconAllEntriesSorted()
    + GetLexicalRelationTypes()
    + GetPublications()
    + PublicationType(publicationName)

### 1.2.2 - 15 Nov 2023

+ Supports Python 3.8 - 3.12
+ Supports FieldWorks 9.0.4 - 9.1.25

### 1.2.1 - 29 Aug 2023

+ Supports Python 3.6 - 3.11
+ Supports FieldWorks 9.0.4 - 9.1.22

+ New FLExProject functions:
    + LexiconFieldIsMultiType() 
    + LexiconFieldIsAnyStringType()
    + LexiconGetSenseNumber()
    + LexiconSenseAnalysesCount()

### 1.2.0 - 16 Aug 2023

+ Moved to pythonnet 3.0.1, which supports FieldWorks 9.1.22

+ FieldWorks dlls no longer need to be included, so the package size 
  has been greatly reduced.

### 1.1.8 - 11 Apr 2023

+ Added LexiconClearField()
+ Updated Set/Get Field functions to handle MultiStrings and a WS 
  parameter (fully backward compatible).

### 1.1.6 - 24 Nov 2022

+ Added the DLLs needed to support FieldWorks 9.1.15/16
+ Added support for Texts to BuildGotoURL()

### 1.1.5 - 15 Oct 2022

+ Constrained pythonnet to < 3 since flexlibs breaks with the new v3.0.0 

### 1.1.3 - 24 Jun 2022

+ FLExProject now requires a CloseProject() call to save data and
  release the lock on the FLEx project.

### 1.1.2 - 20 Jun 2022

+ Configured as a package and published on PyPI
+ Includes .NET DLLs that are needed for compatibility with FLEx 9.0
  through to 9.1.9
  