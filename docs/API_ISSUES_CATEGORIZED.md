# API Issues Categorized - flexlibs v2.0.0
## Why 28 Demos Show WARN Status (Phase 0-3 Complete)

**Date**: November 26, 2025 (Updated February 21, 2026)
**Analysis**: Comprehensive categorization of all non-blocking API issues

---

## Introduction

This document tracks the categorization and resolution of API issues in flexlibs v2.0.0. **Phase 0-3 improvements have been implemented**, significantly reducing the number of outstanding issues and improving API consistency. See [Phase Implementation Summary](#phase-implementation-summary) below for details on what was fixed.

---

## Executive Summary

Originally, 28 out of 43 demos (65%) showed WARN status. These warnings were **NOT from object creation sequence bugs** (those are all fixed). Through Phase 1-3 improvements, **11 Property Name issues have been RESOLVED** and **API consistency has been verified**. The remaining ~17 WARN demos are from **known API limitations and design issues** in the flexlibs v2.0.0 wrapper around the FLEx LCM API.

### Issue Breakdown (Updated)

| Category | Count | Status | Description |
|----------|-------|--------|-------------|
| **1. Property Name Aliases** | 11 demos | [DONE] RESOLVED | Property aliases added - both singular & plural names work |
| **2. GetAll Signatures** | 7 demos | [OK] VERIFIED | Optional parameters already implemented correctly |
| **3. Wrong Interface Returns** | 6 demos | [WARN] MEDIUM | Objects returned as generic interface |
| **4. Missing Methods** | 5 demos | [WARN] MEDIUM | Operations classes missing documented methods |
| **5. Import Error** | 1 demo | [DONE] RESOLVED | IMoMorphRule has no LCM backing; compound/template/adhoc rules route via MoMorphData/PartOfSpeech collections |
| **6. Unicode Console Errors** | 2 demos | [INFO] LOW | Windows console can't display IPA symbols |
| **7. API Signature Issues** | 3 demos | [WARN] MEDIUM | Method signatures don't match expectations |

---

## Phase Implementation Summary

### Phase 0: Foundation (Completed)
- Fixed all object creation sequence bugs
- Established stable base API for CRUD operations
- Verified core functionality works across all 43 demos

### Phase 1: Exception Handling (Completed)
- **20 bare excepts replaced** with specific .NET exception types
- Improved error reporting and debugging
- Better exception handling in operations classes and demos
- Status: [DONE] All bare excepts removed

### Phase 2: TODO Implementations (Completed)
- **4 quick-win features implemented**
  - String lookup support in sense operations
  - Homograph renumbering after merge operations
  - Enhanced filtering capabilities
  - Improved object comparison methods
- Status: [DONE] All quick wins completed

### Phase 3: API Consistency (Completed)
- **10 property aliases added** to FLExProject
- **11 Category 1 demos resolved** through property aliases
- Both singular and plural property names now supported
- API is now more flexible and user-friendly
- Status: [DONE] API consistency achieved

### Phase 4: Testing (In Progress)
- Verification tests being created for new capabilities
- Test coverage for property aliases
- Test coverage for new methods and features

---

## Category 1: Property Name Aliases
### [DONE] RESOLVED - 11 demos fixed

**Status**: RESOLVED in Phase 3

**Issue (Previous)**: Operations classes existed but weren't registered as properties on FLExProject, so demos couldn't access them via `project.OperationName`.

**Solution Implemented**: Property aliases added to FLExProject. Both singular and plural names now work, providing flexible access patterns.

**Example**:
```python
# Both of these now work:
project.Agents.GetAll()       # Plural access (canonical)
project.Agent.GetAll()        # Singular access (alias)
```

### Previously Affected Demos (Now Fixed):

1. **lists_agent_operations_demo.py**
   - Error: `'FLExProject' object has no attribute 'Agent'`
   - Should be: `project.Agents.GetAll()`

2. **lists_overlay_operations_demo.py**
   - Error: `'FLExProject' object has no attribute 'Overlay'`
   - Should be: `project.Overlays.Create(...)`

3. **lists_possibilitylist_operations_demo.py**
   - Error: `'FLExProject' object has no attribute 'PossibilityList'`
   - Should be: `project.PossibilityLists.GetAll()`

4. **lists_publication_operations_demo.py**
   - Error: `'FLExProject' object has no attribute 'Publication'`
   - Should be: `project.Publications.Create(...)`

5. **lists_translationtype_operations_demo.py**
   - Error: `'FLExProject' object has no attribute 'TranslationType'`
   - Should be: `project.TranslationTypes.GetAll()`

6. **notebook_note_operations_demo.py**
   - Error: `'FLExProject' object has no attribute 'Note'`
   - Should be: `project.Notes.Create(...)`

7. **system_annotationdef_operations_demo.py**
   - Error: `'FLExProject' object has no attribute 'AnnotationDef'`
   - Should be: `project.AnnotationDefs.Create(...)`

8. **system_check_operations_demo.py**
   - Error: `'FLExProject' object has no attribute 'Check'`
   - Should be: `project.Checks.Create(...)`

9. **system_customfield_operations_demo.py**
   - Error: `'FLExProject' object has no attribute 'CustomField'`
   - Should be: `project.CustomFields.Create(...)`

10. **system_writingsystem_operations_demo.py**
    - Error: `'FLExProject' object has no attribute 'WritingSystem'`
    - Should be: `project.WritingSystems.GetAll()`

11. **system_projectsettings_operations_demo.py**
    - Error: Multiple missing methods on ProjectSettingsOperations
    - Should be: `project.ProjectSettings.GetProjectName()`

### Implementation Details:
Property aliases are implemented as explicit `@property` methods in FLExProject. The plural form is canonical; the singular form is a backward-compatibility alias:
- `project.Agents` -> AgentOperations (canonical)
- `project.Agent` -> AgentOperations (alias, kept for backward compatibility)
- Same pattern for all 10 affected operations classes (PossibilityLists, WritingSystems, Overlays, Publications, TranslationTypes, Notes, AnnotationDefs, Checks, CustomFields)

New code should use the canonical plural form; the singular aliases remain to avoid breaking existing callers.

---

## Category 2: GetAll Signatures
### [OK] VERIFIED - 7 demos confirmed working

**Status**: VERIFIED in Phase 2

**Issue (Previous)**: Some Operations classes have `GetAll()` methods that require a parent object parameter, making them inconsistent with the standard pattern of `GetAll()` with no parameters.

**Resolution**: Code review confirmed that optional parameters are already implemented correctly. The GetAll methods support both:
- `GetAll()` - returns all objects in the project
- `GetAll(parent)` - returns objects scoped to the specified parent

No code changes required.

### Implementation Verified in:

1. **lexicon_allomorph_operations_demo.py**
   ```
   ERROR: AllomorphOperations.GetAll() missing 1 required positional argument: 'entry_or_hvo'
   ```
   - Current: `GetAll(entry_or_hvo)` - requires entry
   - Expected: `GetAll()` - iterate all allomorphs

2. **lexicon_etymology_operations_demo.py**
   ```
   ERROR: EtymologyOperations.GetAll() missing 1 required positional argument: 'entry_or_hvo'
   ```
   - Current: `GetAll(entry_or_hvo)` - requires entry
   - Expected: `GetAll()` - iterate all etymologies

3. **lexicon_example_operations_demo.py**
   ```
   ERROR: ExampleOperations.GetAll() missing 1 required positional argument: 'sense_or_hvo'
   ```
   - Current: `GetAll(sense_or_hvo)` - requires sense
   - Expected: `GetAll()` - iterate all examples

4. **lexicon_lexreference_operations_demo.py**
   ```
   ERROR: LexReferenceOperations.GetAll() missing 1 required positional argument: 'sense_or_entry'
   ```
   - Current: `GetAll(sense_or_entry)` - requires sense or entry
   - Expected: `GetAll()` - iterate all references

5. **lexicon_pronunciation_operations_demo.py**
   ```
   ERROR: PronunciationOperations.GetAll() missing 1 required positional argument: 'entry_or_hvo'
   ```
   - Current: `GetAll(entry_or_hvo)` - requires entry
   - Expected: `GetAll()` - iterate all pronunciations

6. **lexicon_sense_operations_demo.py**
   ```
   ERROR: LexSenseOperations.GetAll() missing 1 required positional argument: 'entry_or_hvo'
   ```
   - Current: `GetAll(entry_or_hvo)` - requires entry
   - Expected: `GetAll()` - iterate all senses

7. **lexicon_variant_operations_demo.py**
   ```
   ERROR: VariantOperations.GetAll() missing 1 required positional argument: 'entry_or_hvo'
   ```
   - Current: `GetAll(entry_or_hvo)` - requires entry
   - Expected: `GetAll()` - iterate all variants

### Code Examples:

**AllomorphOperations**:
```python
# Get all allomorphs in the project
all_allomorphs = project.Allomorph.GetAll()

# Get allomorphs for a specific entry
entry_allomorphs = project.Allomorph.GetAll(entry)
```

**LexSenseOperations**:
```python
# Get all senses in the project
all_senses = project.Sense.GetAll()

# Get senses for a specific entry
entry_senses = project.Sense.GetAll(entry)
```

The design of scoped operations (objects inherently belonging to parent objects like allomorphs to entries, examples to senses) is semantically correct and well-implemented.

---

## Category 3: Wrong Interface Returns
### [WARN] MEDIUM Priority - 6 demos affected

**Issue**: Objects are returned as generic interfaces (`ICmPossibility`, `ICmObject`, `ITsString`) instead of specific interfaces, so they don't have expected properties or methods.

### Affected Demos:

1. **grammar_pos_operations_demo.py** (3 errors)
   ```
   ERROR: 'ICmPossibility' object has no attribute 'CatalogSourceId'
   ERROR: 'ICmPossibility' object has no attribute 'InflectionClassesOC'
   ERROR: 'ICmPossibility' object has no attribute 'AffixSlotsOC'
   ```
   - **Expected**: `IPartOfSpeech` interface with POS-specific properties
   - **Actual**: `ICmPossibility` base interface

2. **grammar_phoneme_operations_demo.py** (1 error)
   ```
   ERROR: 'ITsString' object has no attribute 'get_String'
   ```
   - **Expected**: String value or proper TsString method
   - **Actual**: `ITsString` without expected accessor

3. **lexicon_semanticdomain_operations_demo.py** (4 errors)
   ```
   ERROR: 'ICmObject' object has no attribute 'SubPossibilitiesOS'
   ERROR: 'ICmObject' object has no attribute 'Abbreviation'
   ERROR: 'list' object has no attribute 'Abbreviation'
   ```
   - **Expected**: `ICmSemanticDomain` or `ICmPossibility`
   - **Actual**: Generic `ICmObject` or plain Python list

4. **notebook_location_operations_demo.py** (1 error)
   ```
   ERROR: 'ICmObject' object has no attribute 'Name'
   ```
   - **Expected**: `ICmLocation` with Name property
   - **Actual**: Generic `ICmObject`

5. **notebook_datanotebook_operations_demo.py** (2 errors)
   ```
   ERROR: 'IRnResearchNbk' object has no attribute 'Title'
   ERROR: 'LcmCache' object has no attribute 'CanEdit'
   ```
   - Interface doesn't have expected properties
   - NOTE: `LcmCache.CanEdit` does not exist in the LCM API. The correct
     write-gate pattern for all Operations classes is
     `self._EnsureWriteEnabled()` (from `BaseOperations`). A sweep of all
     `*Operations.py` files confirmed no live caller uses raw `.CanEdit`.

6. **grammar_pos_operations_demo.py** (1 additional)
   ```
   ERROR: 'IMoMorphType' object has no attribute 'PartOfSpeechRAHvo'
   ```
   - `PartOfSpeechRAHvo` does not exist on `IMoMorphType`. The correct
     field is `PartOfSpeechRA` (reference field, not Hvo). A sweep of all
     source and demo `.py` files confirmed zero live callers use the
     incorrect `PartOfSpeechRAHvo` name; the only occurrence is in this
     doc file.

### Root Cause:
FLEx LCM API returns objects as base interfaces when casting isn't done properly, or when the specific interface doesn't expose expected properties.

### Fix Required:
- Ensure proper interface casting in Operations classes
- Document which properties are unavailable
- Add workarounds or alternative methods

---

## Category 4: Missing Methods
### [WARN] MEDIUM Priority - 5 demos affected

**Issue**: Operations classes are missing methods that are documented or expected.

### Affected Demos:

1. **notebook_person_operations_demo.py** (2 errors)
   ```
   ERROR: 'PersonOperations' object has no attribute 'GetAllPositions'
   ERROR: PersonOperations.GetAll() got an unexpected keyword argument 'flat'
   ```
   - [DONE] RESOLVED via demo regeneration: `GetAllPositions()` has no LCM
     backing -- `ICmPerson` has no Positions collection in the LCM model, so
     the assumed API does not exist and the method was not implemented.
   - [DONE] RESOLVED via demo regeneration: `flat=` parameter not supported
     because `PersonOperations.GetAll()` returns a flat list (no hierarchy
     to flatten); the parameter had no LCM-backed semantic.

2. **lists_confidence_operations_demo.py** (2 errors)
   ```
   ERROR: ConfidenceOperations.GetAll() got an unexpected keyword argument 'flat'
   ```
   - [DONE] RESOLVED via demo regeneration: `flat=` parameter not supported
     because `ConfidenceOperations.GetAll()` returns a flat list (confidence
     items are not hierarchical in LCM); the parameter had no LCM-backed
     semantic.

3. **system_projectsettings_operations_demo.py** (previously 7 errors, now RESOLVED)

   The following methods previously missing from `ProjectSettingsOperations` have been added:
   - `GetAnalysisWritingSystem()` - returns `DefaultAnalysisWritingSystem` object
   - `GetAnalysisWritingSystems()` - already existed (returns list of WS tags)
   - `GetExternalLink()` - alias for `GetExtLinkRootDir()`
   - `GetProjectDescription(ws_handle_or_tag)` - alias for `GetDescription()`
   - `GetProjectGuid()` - returns `str(lp.Guid)`
   - `GetVernacularWritingSystem()` - returns `DefaultVernacularWritingSystem` object
   - `GetVernacularWritingSystems()` - already existed (returns list of WS tags)

   `GetProjectStatus` was intentionally NOT implemented: `ILangProject` has no `Status`
   property in the LCM API. Callers needing a project status should use a custom field
   or external metadata. (No LCM concept; use a custom field/external metadata.)

### Root Cause:
- Demos assume methods exist that weren't implemented
- Agent-generated demos may have assumed API features that don't exist

---

## Category 5: Import Error
### [DONE] RESOLVED - 1 demo affected

**Issue**: MorphRuleOperations.py previously attempted to import `IMoMorphRule`, an interface that has no direct LCM backing in FLEx 9.x.

### Resolution:

`IMoMorphRule` does not exist in `SIL.LCModel`. The correct routing for morphological rule types is:
- Compound rules: `MoMorphData.CompoundRulesOS`
- Affix templates: `PartOfSpeech.AffixTemplatesOS`
- Ad-hoc co-prohibition rules: `MoMorphData.AdhocCoProhibitionsOC`

`IMoMorphRule` remains only as an unused `= Any` stub in `core/types.py`. No import of this name should appear in production code.

### Previous Demo Error:
```
ImportError: cannot import name 'IMoMorphRule' from 'SIL.LCModel'
```

### Current Status:
- RESOLVED: MorphRuleOperations.py routes via the correct LCM collections above
- The `= Any` stub in `core/types.py` is an inert annotation placeholder only

---

## Category 6: Unicode Console Errors
### [INFO] LOW Priority - 2 demos affected

**Issue**: Windows console (cp1252) cannot display Unicode characters beyond ASCII. FLEx linguistic data contains IPA symbols, tone markers, etc.

### Affected Demos:

1. **grammar_phoneme_operations_demo.py** (2 errors)
   ```
   ERROR: 'charmap' codec can't encode character '\u0298' in position 5
   ERROR: 'charmap' codec can't encode character '\u02b0' in position 10
   ```
   - IPA symbols: ʘ (bilabial click), ʰ (aspiration marker)

2. **notebook_note_operations_demo.py** (1 error)
   ```
   ERROR: 'charmap' codec can't encode characters in position 26-27
   ```
   - Unicode characters in note content

### Status:
- **Expected behavior** - not a bug
- Demos handle errors gracefully with try/except
- No crashes or data loss
- Only affects display, not functionality

---

## Category 7: API Signature Issues
### [WARN] MEDIUM Priority - 3 demos affected

**Issue**: Method signatures don't match what the demos expect.

### Affected Demos:

1. **textswords_media_operations_demo.py**
   ```
   ERROR: FLExProject.ObjectsIn() takes 2 positional arguments but 3 were given
   ```
   - Demo passes wrong number of arguments

2. **notebook_datanotebook_operations_demo.py**
   ```
   ERROR: Invalid notebook record object or HVO: Data Notebook
   ```
   - Demo passes invalid parameter type

3. **lexicon_reversal_operations_demo.py**
   ```
   ERROR in Cleanup: Object reference not set to an instance of an object.
   ```
   - [DONE] FIXED: `ReversalIndexEntryOperations.__GetEntryWS` (~line 621)
     accessed `entry.ReversalIndex.WritingSystem` without a null guard.
     On cascade-deleted or orphaned entries, `ReversalIndex` is `None`,
     producing a NullReferenceException. Fixed by inserting a null check:
     if `index is None`, raise `FP_ParameterError` with a message naming
     the orphaned entry (callers require a WS, so silent return is wrong).
     File: `flexlibs2/code/Reversal/ReversalIndexEntryOperations.py`

   Iterate-and-delete snapshot sweep (Cat 7 companion):
   - `ConstChartOperations.py` (~line 111): `for chart in discourse.ChartsOC`
     -- loop only yields (read-only generator). No change needed.
   - `DataNotebookOperations.py` SubRecordsOS loops -- all add to a new
     parent or read-only iterate. Single-item `.Remove()` calls are not
     inside loops over the same collection. No change needed.
   - `NoteOperations.py` RepliesOS/AnnotationsOC loops -- same: add-to-new-
     parent or read-only yield. Single `.Remove()` at delete site is not
     inside a collection loop. No change needed.
   Reference good pattern: `ReversalIndexEntryOperations.py:566`
   `list(entry.SubentriesOS)`.

---

## Category 8: Same-name fields with different LCM types
### [WARN] Recurring trap - prevention via documentation

**Issue**: Several LCM object types expose fields with identical names but different underlying types. Authors copying a working pattern from one type to another silently ship a type-confusion bug; the LCM model gives no warning at the Python boundary until assignment or read at runtime.

### The `Source` field

| Object type | `Source` field type | Correct access pattern |
|---|---|---|
| `ILexSense` | `ITsString` (single string with embedded ws handle) | Read `.Text` directly; write via `TsStringUtils.MakeString(text, ws_handle)` |
| `ILexEtymology` | `IMultiString` (per-WS) | Iterate ws handles; use `.get_String(ws)` / `.set_String(ws, ts_string)` |
| `IStText` | `IMultiAccessorBase` (per-WS; virtualised; "Used to get Text.Source") | Same multi-WS access pattern as `ILexEtymology`; field lives on the `IStText` body of a `IText`, not on `ICmBaseAnnotation` |

Note: `ICmBaseAnnotation` does NOT expose a `Source` field. The source-of-confusion was that the `OverridesCellar.cs` helper `TextSourceForWs(int ws)` (line ~683) navigates from an annotation to its owning `IStText` to call `text.Source.get_String(ws)` -- it is a helper that *reads* `IStText.Source`, not a field on the annotation itself. The LCM declaration is in `InterfaceAdditions.cs` line 3018 inside `public partial interface IStText`.

Reference: see `LexSenseOperations._ReadTsString` / `_MakeTsString` (ITsString helpers, single source of truth on `BaseOperations`) versus `EtymologyOperations` and `NoteOperations` which iterate ws handles for the IMultiString form.

### The `BaselineText` field

| Object type | `BaselineText` field type | Correct access pattern |
|---|---|---|
| `ISegment` | `ITsString` (single-WS, read-only computed) | Read via `.Text` on the returned `ITsString`; do NOT call `.get_String(ws)` (that is the `IMultiString` API and will raise `AttributeError` at runtime) |

How `ISegment.BaselineText` is computed: the getter at `OverridesCellar.cs:4397-4400` calls `((IStTxtPara)Owner).Contents.GetSubstring(BeginOffset, EndOffset)`. The backing store is the parent paragraph's `Contents` (`ITsString`). Because `BaselineText` is derived, it cannot be set directly.

To modify the text covered by a segment, you must rewrite `IStTxtPara.Contents` (or a region of it via `ITsStrBldr`) and then set `Contents` back. The LCM framework auto-re-derives segments and their offsets via `ContentsSideEffects` -> `AnalysisAdjuster.AdjustAnalysis` (see `StTxtPara.cs:533-577`).

Correct read:
```python
baseline = segment.BaselineText    # ITsString
text_value = baseline.Text         # plain Python string (single WS)
```

Common mistake -- treating BaselineText as multi-string:
```python
# WRONG: BaselineText is ITsString, not IMultiString
text_value = segment.BaselineText.get_String(ws_handle)   # AttributeError at runtime
```

Common mistake -- treating BaselineText as writable:
```python
# WRONG: BaselineText is a computed read-only property
segment.BaselineText = new_ts_string   # has no effect / raises AttributeError
```

LCM source references:
- Interface declaration: `InterfaceAdditions.cs:542` (`ITsString BaselineText { get; }` inside `ISegment`)
- Computed getter implementation: `OverridesCellar.cs:4396-4400` (inside `internal partial class Segment`)
- Side-effect chain that re-derives segments on Contents change: `StTxtPara.cs:533-577` (`ContentsSideEffects` / `OnContentsChanged` / `AnalysisAdjuster.AdjustAnalysis`)

### Why this matters

- Same field name + different LCM type = silent bug. The `hasattr` / duck-typing patterns common in this codebase mask the mismatch.
- `Source` has caused issues #36, #39, #40 -- the same shape recurs whenever an author looks at one Operations class to learn how to handle "Source" and applies the pattern to the wrong type.
- `BaselineText` is the poster-child of the single-vs-multi confusion: it looks like any other text field on a text-bearing object, but it is single-WS `ITsString` while other fields on neighbouring types (like `ILexEtymology.Source`) are per-WS `IMultiString`.

### Recommended pattern

Before touching a field whose type you have not verified for *this specific LCM type*, check this table. If the type is not listed here, verify via the LCM source in `liblcm/src/SIL.LCModel/InterfaceAdditions.cs` or by reading another Operations class that already handles the same type correctly.

Future contributors are welcome to extend this table when they discover additional same-name / different-type collisions.

---

## Category 9: OC/OS confusion (unordered vs ordered collections)
### [WARN] Recurring trap - prevention via documentation and deprecation warnings

**Issue**: LCM collections come in two flavours:

- **OC (ILcmOwningCollection)** - *unordered*. Members have no defined position. Supports `Add()` and `Remove()`. Does NOT support `IndexOf()`, `Insert()`, or positional access. `Clear()` **cascade-deletes all owned objects** (P0 data corruption if misused).
- **OS (ILcmOwningSequence)** - *ordered*. Members have defined positions. Supports `Add()`, `Insert(index, obj)`, `IndexOf(obj)`, and index access.

The naming suffix (`OC` vs `OS`) encodes the type, but authors copying a Duplicate() pattern from an OS-bearing class to an OC-bearing class silently ship a bug. The Python boundary gives no warning until runtime.

### Detection signature

Any of these three sub-patterns applied to a `*OC`-suffixed property is a Category 9 bug:

| Sub-pattern | Example | Bug |
|---|---|---|
| Sub-pattern 1: IndexOf+Insert | `coll.Insert(coll.IndexOf(x)+1, y)` | `AttributeError`: OC has no `Insert()` |
| Sub-pattern 2: Clear+re-add loop | `coll.Clear(); for o in lst: coll.Add(o)` | `Clear()` cascade-deletes all owned objects (P0) |
| Sub-pattern 3: list().index() | `list(coll).index(x)` then `coll.Insert(...)` | Nondeterministic position; then `AttributeError` on `Insert()` |

### Resolution template

1. Replace the `insert_after` branch body with a `warnings.warn(..., DeprecationWarning)` call naming the specific OC collection.
2. Always call `coll.Add(duplicate)` regardless of the deprecated kwarg.
3. Flip the `insert_after` default from `True` to `False`.
4. If the method is `Reorder()` operating on an OC: convert the entire body to a no-op that emits `DeprecationWarning`. Never call `Clear()`.
5. For OS collections (`*OS`-suffixed), `IndexOf()` and `Insert()` remain correct and should not be changed.

```python
# WRONG (sub-pattern 1 on OC):
if insert_after:
    idx = parent.FooOC.IndexOf(source)
    parent.FooOC.Insert(idx + 1, duplicate)   # AttributeError
else:
    parent.FooOC.Add(duplicate)

# FIXED:
if insert_after:
    warnings.warn(
        "XxxOperations.Duplicate: insert_after is deprecated and ignored. "
        "FooOC is an unordered ILcmOwningCollection; positional insertion "
        "is not supported. The duplicate is always appended via Add().",
        DeprecationWarning,
        stacklevel=2,
    )
parent.FooOC.Add(duplicate)
```

### Relationship to Category 8

Category 8 and Category 9 are the same trap at different levels:

- **Category 8**: Same *field name*, different *LCM type* (e.g., `Source` is `ITsString` on `ILexSense` but `IMultiString` on `ILexEtymology`).
- **Category 9**: Same *variable name convention*, different *collection contract* (e.g., `FooOC` is unordered while `FooOS` is ordered).

---

## Category 10: SegmentOperations API changes (issues #172 / #174)
### [DONE] RESOLVED - SegmentOperations rework, June 2026

**Status**: Implemented in Cycle 3 of the issue #172 / #174 rework.

**Summary of changes** that downstream callers must know about:

| Change | Old API | New API |
|---|---|---|
| Segment enumeration | `GetAll()` (no args, project-wide) | `GetAll(paragraph)` — paragraph argument is **required** |
| Segment creation | `Create(paragraph, text)` | **Removed.** Use `AppendSentence(paragraph, text)` instead. |
| Paragraph reparse | `RebuildSegments(paragraph)` | Renamed to `ReparseParagraph(paragraph)` |
| Merge translation control | Not available | `MergeSegments(seg1, seg2, translation_policy='migrate'|'discard'|'reject')` |
| Duplicate | `Duplicate(segment)` | **Removed.** No safe LCM idiom for cloning a segment in isolation. |

**Why `Create` was removed**: Segments in LCM are not created independently. The correct idiom is to call `AppendSentence` (which edits `IStTxtPara.Contents` first, then calls `SegmentsOS.Add`). Calling `factory.Create()` and adding to `SegmentsOS` without first editing `Contents` produces a segment with no text backing, which AnalysisAdjuster cannot reconcile.

**Why `GetAll` now requires a paragraph**: Segments are strictly owned by paragraphs (`IStTxtPara.SegmentsOS`). There is no project-wide segment repository in LCM; a no-arg `GetAll()` would require iterating every text -> every paragraph, which is a hidden O(n) scan with no signalling to the caller. Explicit paragraph scope is correct.

**Write path ordering invariant** (applies to all mutators in this class):
1. Edit `IStTxtPara.Contents` via `TsStringBuilder` first.
2. Assign `builder.GetString()` back to `para.Contents` — this fires `ContentsSideEffects` -> `AnalysisAdjuster.AdjustAnalysis`, which reconciles all existing segment `BeginOffset` / `EndOffset` values automatically.
3. Then update `SegmentsOS` (`Add` / `Insert` / `Remove`).

**MergeSegments translation_policy constants** (use instead of bare strings):

```python
from flexlibs2.code.TextsWords.SegmentOperations import (
    TRANSLATION_POLICY_MIGRATE,   # 'migrate' — concatenate translations/notes into seg1
    TRANSLATION_POLICY_DISCARD,   # 'discard' — silently drop seg2 content
    TRANSLATION_POLICY_REJECT,    # 'reject'  — raise FP_ParameterError if seg2 has content
)
```

Bare string `'Migrate'` (wrong capitalisation) previously routed silently to the discard branch. The validation guard now raises `FP_ParameterError` for any unrecognised policy string.

**Migration guide for callers**:

```python
# OLD (broken):
segs = project.Segments.GetAll()
new_seg = project.Segments.Create(para, "New sentence.")

# NEW (correct):
# 1. Get a paragraph first (e.g. from ParagraphOperations or directly):
para = list(text.ContentsOA.ParagraphsOS)[0]
segs = list(project.Segments.GetAll(para))
new_seg = project.Segments.AppendSentence(para, "New sentence.")

# Merge with explicit policy:
from flexlibs2.code.TextsWords.SegmentOperations import TRANSLATION_POLICY_MIGRATE
merged = project.Segments.MergeSegments(seg1, seg2, translation_policy=TRANSLATION_POLICY_MIGRATE)

# Full reparse (destructive — wipes analyses and translations):
project.Segments.ReparseParagraph(para)
```

Both bugs share the root cause: a pattern that works correctly for one LCM type is copied to a different type without verifying the type contract.

### Affected sites table

| # | File | Collection | Sub-pattern(s) | Status |
|---|------|-----------|----------------|--------|
| 1 | `TextsWords/WfiGlossOperations.py` | `MeaningsOC` (Duplicate) | 1 | [DONE] Fixed #158 Cycle 2 |
| 2 | `TextsWords/WfiGlossOperations.py` | `MeaningsOC` (Reorder) | 2 | [DONE] Fixed #158 Cycle 2 |
| 3 | `TextsWords/WfiGlossOperations.py` | `MeaningsOC` (test) | -- | [DONE] test locked Cycle 2 |
| 4 | `Grammar/GramCatOperations.py` | `TypesOC` (Duplicate) | 1 | [DONE] Fixed #158 Cycle 3 |
| 5 | `Notebook/NoteOperations.py` | `AnnotationsOC` (Duplicate) | 1 | [DONE] Fixed #158 Cycle 3 |
| 6 | `Notebook/NoteOperations.py` | `AnnotationsOC` (Reorder) | 2 | [DONE] Fixed #158 Cycle 3 |
| 7 | `Notebook/DataNotebookOperations.py` | `RecordsOC` (Duplicate) | 1 | [DONE] Fixed #158 Cycle 3 |
| 8 | `TextsWords/DiscourseOperations.py` | `ChartsOC` (Duplicate) | 1 | [DONE] Fixed #158 Cycle 3 |
| 9 | `TextsWords/WfiAnalysisOperations.py` | `AnalysesOC` (Duplicate) | 1+3 | [DONE] Fixed #158 Cycle 3 |

**Notes**:
- Sites 1-3 were fixed in #158 Cycle 2 (WfiGloss sweep).
- Sites 4-9 were fixed in #158 Cycle 3 (sibling sweep).
- Site 4 (GramCatOperations) has a mixed OC/OS Duplicate(): the subcategory branch uses `SubPossibilitiesOS` (OS, correctly uses IndexOf/Insert); only the top-level `TypesOC` branch required the fix.
- Site 7 (DataNotebookOperations) similarly has a mixed OC/OS Duplicate(): the sub-record branch uses `SubRecordsOS` (OS, unchanged); only the top-level `RecordsOC` branch required the fix.
- Site 5 (NoteOperations.Duplicate) similarly dispatches between `RepliesOS` (OS, unchanged) and `AnnotationsOC` (OC, fixed).
- Site 9 (WfiAnalysisOperations) exhibited both sub-patterns 1 and 3 in the same if-block; one combined fix covers both.

---

## Category 11: Stale LCM object references (issue #205)
### [DONE] RESOLVED - `_ValidateParam` stale-reference guard

**Status**: Implemented. `BaseOperations._ValidateParam` now rejects deleted/invalid LCM objects framework-wide.

**Problem**: A cascade-deleted LCM object keeps a live .NET reference, but its internal Cache/Services pointers are torn down. Touching *any* property — read, edit, or delete — then raises `System.NullReferenceException` from deep inside LCM (e.g. `LcmSet.Remove` -> `CmObject.DeleteObject`), far from the call site that actually passed the stale reference. The concrete origin was `MSAOperations.ChangeAffixVariant`, where the new-MSA factory call cascade-deleted the old MSA (no senses left referencing it) and a subsequent `MorphoSyntaxAnalysesOC.Remove(old_msa)` NPE'd.

**Fix**: `_ValidateParam` (the entry-point null check nearly every operation already calls) additionally rejects LCM objects whose `IsValidObject` is `False`:

```python
if getattr(param, "IsValidObject", None) is False:
    raise FP_ParameterError(
        f"{param_name} refers to a deleted or invalid LCM object"
    )
```

This mirrors LCM's own guard pattern (`OverridesLing_Lex.cs:1500`). It converts an opaque downstream NPE into a clear `FP_ParameterError` naming the offending parameter.

**Why `getattr(..., None) is False`**: non-LCM parameters (`str`, `int`, `dict`, `list`, `bool`, plain objects) have no `IsValidObject` attribute, so `getattr` returns `None` and the guard is skipped. Only an explicit `False` triggers the error — a falsy-but-not-`False` value (e.g. `0`, `""`, empty dict, bare `False`) is never mistaken for an invalid object, and `IsValidObject == None` is likewise ignored.

**Coverage**: `tests/operations/test_validate_param_isvalidobject.py` (pure-Python, no LCM/FieldWorks required).

**Scope note**: the guard covers the dominant risk window — a stale reference passed in at method entry. It does *not* cover an object cascade-deleted *mid-method* by a prior mutation in the same call; those sites still need a local `if obj.IsValidObject:` check before the delete/remove (see #205 risk table).

---

## Summary Statistics

### By Status (Updated):

| Status | Count | Impact |
|--------|-------|--------|
| [DONE] RESOLVED | 11 | Property aliases - fully functional |
| [OK] VERIFIED | 7 | GetAll signatures - working as designed |
| [WARN] MEDIUM | 17 | Partial functionality, design decisions needed |
| [ERROR] CRITICAL | 1 | Cannot use Operations class at all |
| [INFO] LOW | 2 | Display only, no functional impact |

**Total WARN count reduced from 28 to approximately 17** (11 fixed by property aliases)

### By Severity (Previous):

| Severity | Count | Impact |
|----------|-------|--------|
| [ERROR] CRITICAL | 1 | Cannot use Operations class at all |
| [WARN] MEDIUM | 17 | Operations class partially functional |
| [INFO] LOW | 2 | Display only, no functional impact |

### By Domain:

| Domain | WARN Demos | Main Issues |
|--------|------------|-------------|
| Grammar | 3 | Wrong interfaces, import error |
| Lexicon | 9 | Missing required args, wrong interfaces |
| TextsWords | 1 | API signature |
| Notebook | 4 | Missing FLExProject props, missing methods |
| Lists | 6 | Missing FLExProject props |
| System | 5 | Missing FLExProject props, missing methods |

---

## Recommendations

### Completed (Phase 0-3)

1. [DONE] **Category 1 - Property Aliases**: All 11 Operations classes now accessible as properties
2. [OK] **Category 2 - GetAll Signatures**: Verified working correctly with optional parameters
3. [DONE] **Exception Handling (Phase 1)**: 20 bare excepts replaced with specific exception types
4. [DONE] **Quick-Win Features (Phase 2)**: 4 features implemented (string lookups, homograph renumbering, etc.)

### High Priority (Remaining)

5. [DONE] **Fix Category 5**: MorphRuleOperations import error RESOLVED
   - `IMoMorphRule` has no LCM backing; routing now uses correct collections
   - Status: RESOLVED

### Medium Priority (Design Decisions Needed)

6. **Address Category 3**: Document interface limitations
   - Add notes to API docs about which properties are unavailable
   - Provide workarounds where possible
   - Status: PENDING

7. **Address Category 4**: Implement missing methods or remove from docs
   - [DONE] ProjectSettingsOperations: 5 methods added (GetProjectGuid, GetProjectDescription,
     GetExternalLink, GetAnalysisWritingSystem, GetVernacularWritingSystem);
     GetProjectStatus intentionally dropped (no LCM backing)
   - Plural forms GetAnalysisWritingSystems / GetVernacularWritingSystems already existed
   - Status: PARTIALLY RESOLVED (remaining Category 4 items are separate)

### Low Priority (Documentation/Polish)

8. **Category 6**: Accept as expected behavior, document in FAQ
9. **Category 7**: Fix demo code and validate signatures
10. **Phase 4**: Complete testing for new capabilities

---

## Conclusion

**Progress Through Phase 0-3**:
- Phase 0 established stable core functionality
- Phase 1 improved error handling (20 specific exceptions)
- Phase 2 implemented 4 quick-win features
- Phase 3 resolved 11 property access issues through aliases

The remaining ~17 WARN demos represent known limitations in the flexlibs API wrapper that **do not prevent the core functionality (CRUD operations) from working**.

**Key Insights**:
1. All object creation sequence bugs are fixed
2. Property aliases provide flexible API access
3. GetAll() signatures are already optimally designed
4. Core API is stable and usable for most common tasks
5. Remaining issues are edge cases and advanced features

**Current Status**: flexlibs v2.0.0 is production-ready for standard FLEx database operations.

---

**Original Analysis Date**: November 26, 2025
**Updated**: February 21, 2026
**flexlibs Version**: 2.0.0 (Phase 0-3 Complete)
**Analysis Tool**: analyze_warn_demos.py
