# Reversal & Wordform Operations Test Specifications

## Overview

This document provides detailed test specifications for all 6 Reversal and Wordform Operations classes in flexicon. These classes handle reversal indexes, wordform analysis, morpheme breakdown, and glossing.

**Test Scope**: 6 Reversal & Wordform Operations classes
**Related Classes**: LexSenseOperations, LexEntryOperations, TextOperations

---

## Table of Contents

1. [ReversalIndexOperations Tests](#reversalindexoperations-tests)
2. [ReversalEntryOperations Tests](#reversalentryoperations-tests)
3. [ReversalSubentryOperations Tests](#reversalsubentryoperations-tests)
4. [WfiAnalysisOperations Tests](#wfianalysisoperations-tests)
5. [WfiMorphBundleOperations Tests](#wfimorphbundleoperations-tests)
6. [WfiGlossOperations Tests](#wfiglossoperations-tests)

---

## ReversalIndexOperations Tests

### Class Information
- **LCM Interface**: IReversalIndex
- **Parent**: LexDb (ILexDb.ReversalIndexesOC)
- **Children**: Entries (IReversalIndex.EntriesOC), PartsOfSpeech
- **Key Properties**: WritingSystem (string), Name (MultiUnicode)

### Test_GetAllIndexes

**Setup**:
```python
project = FLExProject()
project.OpenProject("TestProject", writeEnabled=True)
```

**Action**:
```python
indexes = list(project.ReversalIndexes.GetAllIndexes())
```

**Verify**:
- `len(indexes) >= 0` (may have 0 or more)
- Returns iterator over all reversal indexes

### Test_GetIndex_Existing

**Setup**:
```python
# Assuming English reversal index exists or is created
# May need to create one first in FLEx GUI or via code
```

**Action**:
```python
en_index = project.ReversalIndexes.GetIndex("en")
```

**Verify**:
- `en_index is not None` (if English index exists)
- `en_index.WritingSystem == "en"`

### Test_GetIndex_NonExistent

**Action**:
```python
fake_index = project.ReversalIndexes.GetIndex("zz-fake")
```

**Verify**:
- `fake_index is None` (returns None, not exception)

### Test_Create_ReversalIndex

**Action**:
```python
index = project.ReversalIndexes.Create("fr", name="French Reversal")
```

**Verify**:
- `index is not None`
- `index.WritingSystem == "fr"`
- `project.ReversalIndexes.GetName(index) == "French Reversal"`
- Index in project's ReversalIndexesOC

### Test_Create_NullWritingSystem

**Action**:
```python
index = project.ReversalIndexes.Create(None, "Test")
```

**Verify**:
- Raises FP_NullParameterError

### Test_Create_InvalidWritingSystem

**Action**:
```python
index = project.ReversalIndexes.Create("invalid-ws-tag", "Test")
```

**Verify**:
- Either: Raises FP_ParameterError
- Or: Creates index with warning (document behavior)

### Test_GetName

**Setup**:
```python
index = project.ReversalIndexes.Create("en", name="English Reversal")
```

**Action**:
```python
name = project.ReversalIndexes.GetName(index)
```

**Verify**:
- `name == "English Reversal"`

### Test_SetName

**Action**:
```python
project.ReversalIndexes.SetName(index, "New Name")
```

**Verify**:
- `project.ReversalIndexes.GetName(index) == "New Name"`

### Test_GetWritingSystem

**Setup**:
```python
index = project.ReversalIndexes.Create("es", "Spanish")
```

**Action**:
```python
ws = project.ReversalIndexes.GetWritingSystem(index)
```

**Verify**:
- `ws == "es"`

### Test_Delete_Index

**Setup**:
```python
index = project.ReversalIndexes.Create("test", "Test Index")
index_guid = index.Guid
```

**Action**:
```python
project.ReversalIndexes.Delete(index)
```

**Verify**:
- Index removed from project
- Index no longer accessible by GUID

### Test_Delete_CascadeEntries

**Setup**:
```python
index = project.ReversalIndexes.Create("test", "Test Index")
entry = project.ReversalEntries.Create(index, "test entry")
entry_guid = entry.Guid
```

**Action**:
```python
project.ReversalIndexes.Delete(index)
```

**Verify**:
- Entry also deleted (cascade)
- Entry no longer accessible by GUID

---

## ReversalEntryOperations Tests

### Class Information
- **LCM Interface**: IReversalIndexEntry
- **Parent**: ReversalIndex (IReversalIndex.EntriesOC) or parent entry (SubentriesOS)
- **Children**: Subentries (IReversalIndexEntry.SubentriesOS)
- **Key Properties**: ReversalForm (MultiString), SensesRS (references to ILexSense)

### Test_Create_MinimalEntry

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
if not index:
    index = project.ReversalIndexes.Create("en", "English")
```

**Action**:
```python
entry = project.ReversalEntries.Create(index, form="run")
```

**Verify**:
- `entry is not None`
- `entry.Owner == index` or `entry in index.EntriesOC`
- `project.ReversalEntries.GetForm(entry) == "run"`
- `entry.Guid != System.Guid.Empty`

### Test_Create_NullIndex

**Action**:
```python
entry = project.ReversalEntries.Create(None, "test")
```

**Verify**:
- Raises FP_NullParameterError

### Test_Create_NullForm

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
```

**Action**:
```python
entry = project.ReversalEntries.Create(index, form=None)
```

**Verify**:
- Raises FP_NullParameterError

### Test_Create_EmptyForm

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
```

**Action**:
```python
entry = project.ReversalEntries.Create(index, form="")
```

**Verify**:
- Raises FP_ParameterError

### Test_Find_ExistingEntry

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
created_entry = project.ReversalEntries.Create(index, "walk")
```

**Action**:
```python
found_entry = project.ReversalEntries.Find(index, "walk")
```

**Verify**:
- `found_entry is not None`
- `found_entry.Hvo == created_entry.Hvo`

### Test_Find_NonExistentEntry

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
```

**Action**:
```python
found_entry = project.ReversalEntries.Find(index, "nonexistent")
```

**Verify**:
- `found_entry is None`

### Test_GetAll_ForIndex

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
project.ReversalEntries.Create(index, "entry1")
project.ReversalEntries.Create(index, "entry2")
```

**Action**:
```python
entries = list(project.ReversalEntries.GetAll(index))
```

**Verify**:
- `len(entries) >= 2`
- Created entries in collection

### Test_GetAll_Empty

**Setup**:
```python
index = project.ReversalIndexes.Create("test", "Test")
# No entries yet
```

**Action**:
```python
entries = list(project.ReversalEntries.GetAll(index))
```

**Verify**:
- `len(entries) == 0`

### Test_GetForm

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
entry = project.ReversalEntries.Create(index, "test")
```

**Action**:
```python
form = project.ReversalEntries.GetForm(entry)
```

**Verify**:
- `form == "test"`

### Test_SetForm

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
entry = project.ReversalEntries.Create(index, "old form")
```

**Action**:
```python
project.ReversalEntries.SetForm(entry, "new form")
```

**Verify**:
- `project.ReversalEntries.GetForm(entry) == "new form"`

### Test_AddSense

**Setup**:
```python
# Create lexical entry with sense
lex_entry = project.LexEntry.Create("run")
sense = lex_entry.SensesOS[0]  # Assuming Create adds blank sense
project.Senses.SetGloss(sense, "to move rapidly")

# Create reversal entry
index = project.ReversalIndexes.GetIndex("en")
rev_entry = project.ReversalEntries.Create(index, "run")
```

**Action**:
```python
project.ReversalEntries.AddSense(rev_entry, sense)
```

**Verify**:
- `sense in rev_entry.SensesRS`
- Bidirectional link: `rev_entry in sense.ReferringReversalIndexEntries`

### Test_RemoveSense

**Setup**:
```python
# From previous test
project.ReversalEntries.AddSense(rev_entry, sense)
```

**Action**:
```python
project.ReversalEntries.RemoveSense(rev_entry, sense)
```

**Verify**:
- `sense not in rev_entry.SensesRS`
- Bidirectional link removed: `rev_entry not in sense.ReferringReversalIndexEntries`

### Test_GetSenses

**Setup**:
```python
lex_entry = project.LexEntry.Create("walk")
sense1 = lex_entry.SensesOS[0]
sense2 = project.Senses.Create(lex_entry, "walking motion")

index = project.ReversalIndexes.GetIndex("en")
rev_entry = project.ReversalEntries.Create(index, "walk")
project.ReversalEntries.AddSense(rev_entry, sense1)
project.ReversalEntries.AddSense(rev_entry, sense2)
```

**Action**:
```python
senses = project.ReversalEntries.GetSenses(rev_entry)
```

**Verify**:
- `len(senses) == 2`
- Both senses in collection

### Test_Delete_Entry

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
entry = project.ReversalEntries.Create(index, "delete me")
entry_guid = entry.Guid
```

**Action**:
```python
project.ReversalEntries.Delete(entry)
```

**Verify**:
- Entry removed from index.EntriesOC
- Entry no longer accessible by GUID

### Test_Delete_UnlinksSenses

**Setup**:
```python
lex_entry = project.LexEntry.Create("test")
sense = lex_entry.SensesOS[0]

index = project.ReversalIndexes.GetIndex("en")
rev_entry = project.ReversalEntries.Create(index, "test")
project.ReversalEntries.AddSense(rev_entry, sense)
```

**Action**:
```python
project.ReversalEntries.Delete(rev_entry)
```

**Verify**:
- Reversal entry deleted
- Sense still exists (not cascade deleted)
- Sense no longer references deleted reversal entry

### Test_Integration_BidirectionalSenseLinking

**Setup**:
```python
# Create lexical entry and sense
lex_entry = project.LexEntry.Create("run")
sense = lex_entry.SensesOS[0]
project.Senses.SetGloss(sense, "to move rapidly")

# Create reversal entry
index = project.ReversalIndexes.GetIndex("en")
rev_entry = project.ReversalEntries.Create(index, "run")
```

**Action**:
```python
# Link reversal to sense
project.ReversalEntries.AddSense(rev_entry, sense)
```

**Verify**:
- Forward link: `sense in rev_entry.SensesRS`
- Backward link: `rev_entry in sense.ReferringReversalIndexEntries`
- Bidirectional link maintained

**Action 2**:
```python
# Remove link
project.ReversalEntries.RemoveSense(rev_entry, sense)
```

**Verify**:
- Forward link removed: `sense not in rev_entry.SensesRS`
- Backward link removed: `rev_entry not in sense.ReferringReversalIndexEntries`
- Both sides cleaned up

---

## ReversalSubentryOperations Tests

### Class Information
- **LCM Interface**: IReversalIndexEntry (same as entry, but nested)
- **Parent**: ReversalEntry (IReversalIndexEntry.SubentriesOS)
- **Key Properties**: Same as ReversalEntry (ReversalForm, SensesRS)

### Test_Create_Subentry

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
parent_entry = project.ReversalEntries.Create(index, "run")
```

**Action**:
```python
subentry = project.ReversalSubentries.Create(parent_entry, "running")
```

**Verify**:
- `subentry is not None`
- `subentry.Owner == parent_entry`
- `subentry in parent_entry.SubentriesOS`
- `project.ReversalSubentries.GetForm(subentry) == "running"`

### Test_Create_NullParent

**Action**:
```python
subentry = project.ReversalSubentries.Create(None, "test")
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetParentEntry

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
parent = project.ReversalEntries.Create(index, "parent")
subentry = project.ReversalSubentries.Create(parent, "child")
```

**Action**:
```python
retrieved_parent = project.ReversalSubentries.GetParentEntry(subentry)
```

**Verify**:
- `retrieved_parent.Hvo == parent.Hvo`

### Test_GetSubentries

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
parent = project.ReversalEntries.Create(index, "parent")
sub1 = project.ReversalSubentries.Create(parent, "child1")
sub2 = project.ReversalSubentries.Create(parent, "child2")
```

**Action**:
```python
subs = project.ReversalSubentries.GetSubentries(parent)
```

**Verify**:
- `len(subs) == 2`
- Both subentries in collection

### Test_Delete_Subentry

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
parent = project.ReversalEntries.Create(index, "parent")
subentry = project.ReversalSubentries.Create(parent, "child")
sub_guid = subentry.Guid
```

**Action**:
```python
project.ReversalSubentries.Delete(subentry)
```

**Verify**:
- Subentry removed from parent.SubentriesOS
- Subentry no longer accessible by GUID
- Parent entry still exists

### Test_NestedSubentries

**Setup**:
```python
index = project.ReversalIndexes.GetIndex("en")
parent = project.ReversalEntries.Create(index, "level1")
sub1 = project.ReversalSubentries.Create(parent, "level2")
sub2 = project.ReversalSubentries.Create(sub1, "level3")
```

**Verify**:
- `sub1.Owner == parent`
- `sub2.Owner == sub1`
- `sub1 in parent.SubentriesOS`
- `sub2 in sub1.SubentriesOS`
- Three-level nesting works

---

## WfiAnalysisOperations Tests

### Class Information
- **LCM Interface**: IWfiAnalysis
- **Parent**: Wordform (IWfiWordform.AnalysesOC)
- **Children**: MorphBundles (IWfiAnalysis.MorphBundlesOS), Meanings
- **Key Properties**: CategoryRA, AgentOpinion (human vs. parser), Approved

### Test_Create_Analysis

**Setup**:
```python
# Create or find wordform
wordform = project.Wordforms.Create("running")
```

**Action**:
```python
analysis = project.WfiAnalyses.Create(wordform)
```

**Verify**:
- `analysis is not None`
- `analysis.Owner == wordform`
- `analysis in wordform.AnalysesOC`
- `analysis.Guid != System.Guid.Empty`

### Test_Create_NullWordform

**Action**:
```python
analysis = project.WfiAnalyses.Create(None)
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetAll_ForWordform

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis1 = project.WfiAnalyses.Create(wordform)
analysis2 = project.WfiAnalyses.Create(wordform)
```

**Action**:
```python
analyses = list(project.WfiAnalyses.GetAll(wordform))
```

**Verify**:
- `len(analyses) == 2`
- Both analyses in collection

### Test_GetWordform

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
```

**Action**:
```python
retrieved_wf = project.WfiAnalyses.GetWordform(analysis)
```

**Verify**:
- `retrieved_wf.Hvo == wordform.Hvo`

### Test_GetApproved

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
```

**Action**:
```python
project.WfiAnalyses.SetApproved(analysis, True)
approved = project.WfiAnalyses.GetApproved(analysis)
```

**Verify**:
- `approved == True`

### Test_SetApproved

**Action**:
```python
project.WfiAnalyses.SetApproved(analysis, False)
```

**Verify**:
- `project.WfiAnalyses.GetApproved(analysis) == False`

### Test_GetCategory

**Setup**:
```python
wordform = project.Wordforms.Create("running")
analysis = project.WfiAnalyses.Create(wordform)
# Get or create POS
pos = project.POS.Find("Verb") or project.POS.Create("Verb")
```

**Action**:
```python
project.WfiAnalyses.SetCategory(analysis, pos)
category = project.WfiAnalyses.GetCategory(analysis)
```

**Verify**:
- `category.Hvo == pos.Hvo`

### Test_AddMorphBundle

**Setup**:
```python
wordform = project.Wordforms.Create("running")
analysis = project.WfiAnalyses.Create(wordform)
```

**Action**:
```python
bundle = project.WfiAnalyses.AddMorphBundle(analysis)
```

**Verify**:
- `bundle is not None`
- `bundle.Owner == analysis`
- `bundle in analysis.MorphBundlesOS`

### Test_GetMorphBundles

**Setup**:
```python
wordform = project.Wordforms.Create("running")
analysis = project.WfiAnalyses.Create(wordform)
bundle1 = project.WfiAnalyses.AddMorphBundle(analysis)
bundle2 = project.WfiAnalyses.AddMorphBundle(analysis)
```

**Action**:
```python
bundles = project.WfiAnalyses.GetMorphBundles(analysis)
```

**Verify**:
- `len(bundles) == 2`
- Both bundles in collection

### Test_Delete_Analysis

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
analysis_guid = analysis.Guid
```

**Action**:
```python
project.WfiAnalyses.Delete(analysis)
```

**Verify**:
- Analysis removed from wordform.AnalysesOC
- Analysis no longer accessible by GUID

### Test_Delete_CascadeMorphBundles

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
bundle = project.WfiAnalyses.AddMorphBundle(analysis)
bundle_guid = bundle.Guid
```

**Action**:
```python
project.WfiAnalyses.Delete(analysis)
```

**Verify**:
- Morph bundle also deleted (cascade)
- Bundle no longer accessible by GUID

---

## WfiMorphBundleOperations Tests

### Class Information
- **LCM Interface**: IWfiMorphBundle
- **Parent**: Analysis (IWfiAnalysis.MorphBundlesOS)
- **Key Properties**: MorphRA (allomorph), SenseRA (lexical sense), MsaRA (morphosyntactic analysis)

### Test_Create_MorphBundle

**Setup**:
```python
wordform = project.Wordforms.Create("running")
analysis = project.WfiAnalyses.Create(wordform)
```

**Action**:
```python
bundle = project.WfiMorphBundles.Create(analysis)
```

**Verify**:
- `bundle is not None`
- `bundle.Owner == analysis`
- `bundle in analysis.MorphBundlesOS`

### Test_Create_NullAnalysis

**Action**:
```python
bundle = project.WfiMorphBundles.Create(None)
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetAnalysis

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
bundle = project.WfiMorphBundles.Create(analysis)
```

**Action**:
```python
retrieved_analysis = project.WfiMorphBundles.GetAnalysis(bundle)
```

**Verify**:
- `retrieved_analysis.Hvo == analysis.Hvo`

### Test_SetSense

**Setup**:
```python
# Create lexical entry and sense
lex_entry = project.LexEntry.Create("run")
sense = lex_entry.SensesOS[0]

# Create morph bundle
wordform = project.Wordforms.Create("run")
analysis = project.WfiAnalyses.Create(wordform)
bundle = project.WfiMorphBundles.Create(analysis)
```

**Action**:
```python
project.WfiMorphBundles.SetSense(bundle, sense)
```

**Verify**:
- `bundle.SenseRA == sense`
- Bundle links to lexicon

### Test_GetSense

**Setup**:
```python
# From previous test
project.WfiMorphBundles.SetSense(bundle, sense)
```

**Action**:
```python
retrieved_sense = project.WfiMorphBundles.GetSense(bundle)
```

**Verify**:
- `retrieved_sense.Hvo == sense.Hvo`

### Test_SetMorph

**Setup**:
```python
# Create lexical entry with allomorph
lex_entry = project.LexEntry.Create("run")
allomorph = lex_entry.LexemeFormOA

wordform = project.Wordforms.Create("run")
analysis = project.WfiAnalyses.Create(wordform)
bundle = project.WfiMorphBundles.Create(analysis)
```

**Action**:
```python
project.WfiMorphBundles.SetMorph(bundle, allomorph)
```

**Verify**:
- `bundle.MorphRA == allomorph`

### Test_GetMorph

**Action**:
```python
retrieved_morph = project.WfiMorphBundles.GetMorph(bundle)
```

**Verify**:
- `retrieved_morph.Hvo == allomorph.Hvo`

### Test_Delete_Bundle

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
bundle = project.WfiMorphBundles.Create(analysis)
bundle_guid = bundle.Guid
```

**Action**:
```python
project.WfiMorphBundles.Delete(bundle)
```

**Verify**:
- Bundle removed from analysis.MorphBundlesOS
- Bundle no longer accessible by GUID

### Test_Integration_WordformToLexiconLinking

**Setup**:
```python
# Create lexical entry "run" + "ing"
run_entry = project.LexEntry.Create("run")
run_sense = run_entry.SensesOS[0]
project.Senses.SetGloss(run_sense, "to move rapidly")

ing_entry = project.LexEntry.Create("-ing", morph_type="suffix")
ing_sense = ing_entry.SensesOS[0]
project.Senses.SetGloss(ing_sense, "present participle")

# Create wordform analysis
wordform = project.Wordforms.Create("running")
analysis = project.WfiAnalyses.Create(wordform)
```

**Action**:
```python
# Add bundles for root and suffix
bundle_run = project.WfiMorphBundles.Create(analysis)
project.WfiMorphBundles.SetSense(bundle_run, run_sense)
project.WfiMorphBundles.SetMorph(bundle_run, run_entry.LexemeFormOA)

bundle_ing = project.WfiMorphBundles.Create(analysis)
project.WfiMorphBundles.SetSense(bundle_ing, ing_sense)
project.WfiMorphBundles.SetMorph(bundle_ing, ing_entry.LexemeFormOA)
```

**Verify**:
- `analysis.MorphBundlesOS.Count == 2`
- `bundle_run.SenseRA == run_sense`
- `bundle_ing.SenseRA == ing_sense`
- Full morpheme breakdown links to lexicon
- Analysis represents "run" + "-ing" = "running"

---

## WfiGlossOperations Tests

### Class Information
- **LCM Interface**: IWfiGloss
- **Parent**: Analysis (IWfiAnalysis.MeaningsOC)
- **Key Properties**: Form (MultiUnicode - the gloss text itself)

### Test_Create_Gloss

**Setup**:
```python
wordform = project.Wordforms.Create("running")
analysis = project.WfiAnalyses.Create(wordform)
```

**Action**:
```python
gloss = project.WfiGlosses.Create(analysis, "running", wsHandle="en")
```

**Verify**:
- `gloss is not None`
- `gloss.Owner == analysis`
- `gloss in analysis.MeaningsOC`
- `project.WfiGlosses.GetForm(gloss, "en") == "running"`

### Test_Create_NullAnalysis

**Action**:
```python
gloss = project.WfiGlosses.Create(None, "test")
```

**Verify**:
- Raises FP_NullParameterError

### Test_Create_NullForm

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
```

**Action**:
```python
gloss = project.WfiGlosses.Create(analysis, None)
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetForm

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
gloss = project.WfiGlosses.Create(analysis, "test gloss", "en")
```

**Action**:
```python
form = project.WfiGlosses.GetForm(gloss, "en")
```

**Verify**:
- `form == "test gloss"`

### Test_SetForm

**Action**:
```python
project.WfiGlosses.SetForm(gloss, "new gloss", "en")
```

**Verify**:
- `project.WfiGlosses.GetForm(gloss, "en") == "new gloss"`

### Test_GetForm_MultipleWritingSystems

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
gloss = project.WfiGlosses.Create(analysis, "test gloss", "en")
project.WfiGlosses.SetForm(gloss, "glosa de prueba", "es")
```

**Action**:
```python
form_en = project.WfiGlosses.GetForm(gloss, "en")
form_es = project.WfiGlosses.GetForm(gloss, "es")
```

**Verify**:
- `form_en == "test gloss"`
- `form_es == "glosa de prueba"`
- MultiString supports multiple WS

### Test_GetAnalysis

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
gloss = project.WfiGlosses.Create(analysis, "test", "en")
```

**Action**:
```python
retrieved_analysis = project.WfiGlosses.GetAnalysis(gloss)
```

**Verify**:
- `retrieved_analysis.Hvo == analysis.Hvo`

### Test_Delete_Gloss

**Setup**:
```python
wordform = project.Wordforms.Create("test")
analysis = project.WfiAnalyses.Create(wordform)
gloss = project.WfiGlosses.Create(analysis, "test", "en")
gloss_guid = gloss.Guid
```

**Action**:
```python
project.WfiGlosses.Delete(gloss)
```

**Verify**:
- Gloss removed from analysis.MeaningsOC
- Gloss no longer accessible by GUID

---

## Integration Test Scenarios

### Scenario 1: Complete Reversal Index Creation

**Objective**: Create reversal index with entries linked to senses.

**Steps**:
1. Create or get English reversal index
2. Create reversal entry "run"
3. Create reversal entry "walk"
4. Create lexical entries "run" and "walk" (if not exist)
5. Link reversal "run" to lexical sense "run"
6. Link reversal "walk" to lexical sense "walk"
7. Create subentry "running" under "run"
8. Verify bidirectional links
9. Open in FLEx GUI and verify display

**Expected Results**:
- Reversal index displays in reversal view
- Entries appear alphabetically
- Subentries nested correctly
- Clicking entry shows linked senses
- Clicking sense shows referring reversal entries

### Scenario 2: Complete Wordform Analysis Workflow

**Objective**: Analyze wordform into morphemes and link to lexicon.

**Steps**:
1. Create wordform "running"
2. Create analysis for wordform
3. Create morph bundle for root "run"
4. Link bundle to lexical entry "run"
5. Create morph bundle for suffix "-ing"
6. Link bundle to lexical entry "-ing"
7. Create gloss "running" for analysis
8. Mark analysis as human-approved
9. Verify in FLEx Text & Words
10. Create alternative analysis (different parse)
11. Verify both analyses appear

**Expected Results**:
- Wordform shows in wordform inventory
- Analysis shows morpheme breakdown
- Bundles link correctly to lexicon
- Gloss displays in analysis language
- Human approval flag works
- Multiple analyses supported

### Scenario 3: Reversal Entry with Multiple Senses

**Objective**: Test one reversal entry linking to multiple senses.

**Steps**:
1. Create reversal index
2. Create reversal entry "bank"
3. Create lexical entry "bank" (financial)
4. Create sense "financial institution"
5. Create lexical entry "bank" (river)
6. Create sense "edge of river"
7. Link reversal "bank" to both senses
8. Verify both links maintained
9. Remove one link
10. Verify other link intact

**Expected Results**:
- Reversal entry links to multiple senses
- Both senses accessible from reversal
- Both reversals visible from senses
- Link removal selective (doesn't affect other)
- No data corruption

---

## Test Execution Notes

### Prerequisites
- FLEx test project with lexicon
- At least one reversal index (English)
- Sample texts for wordform testing
- Write-enabled access

### Common Setup
```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("TestProject_Reversal_Wordform", writeEnabled=True)

# Ensure English reversal index exists
en_index = project.ReversalIndexes.GetIndex("en")
if not en_index:
    en_index = project.ReversalIndexes.Create("en", "English Reversal")
```

### Common Teardown
```python
# Clean up
project.CloseProject()
```

### Test Data
- Simple English reversal entries (run, walk, house, etc.)
- Basic wordforms (running, walked, houses, etc.)
- Morphemes: roots + common affixes (-ing, -ed, -s, etc.)

---

## Test Status Summary

| Class | Tests Specified | Tests Implemented | Tests Passing | Coverage |
|-------|----------------|-------------------|---------------|----------|
| ReversalIndexOperations | 11 | 0 | 0 | 0% |
| ReversalEntryOperations | 17 | 0 | 0 | 0% |
| ReversalSubentryOperations | 6 | 0 | 0 | 0% |
| WfiAnalysisOperations | 12 | 0 | 0 | 0% |
| WfiMorphBundleOperations | 10 | 0 | 0 | 0% |
| WfiGlossOperations | 9 | 0 | 0 | 0% |
| **Total** | **65** | **0** | **0** | **0%** |

---

**Document Version**: 1.0
**Last Updated**: 2025-12-05
**Status**: Draft - Awaiting Implementation
