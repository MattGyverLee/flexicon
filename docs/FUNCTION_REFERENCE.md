# FlexLibs v2.0.0 - Comprehensive Function Reference

**Last refreshed:** 2026-05-27 — Phase 5/6 additions integrated.

## Overview
This document lists ALL functions in flexlibs (v2.0 through v2.4+), organized by implementation phase. For each function, we identify:
- The method name (e.g., `project.LexEntry.Create()`)
- The LibLCM function(s) it replaces/wraps

The original 14 phases (the v2.0.0 baseline) are documented unchanged below. Public-method additions made in **Phase 5/6 and later** (alpha-feature constraints + the WireRule composer, feature-based natural classes, IPA management on phonemes, the phonological-feature system, expanded inflection-feature surface, MSA creation, catalog imports for the major reference lists, and several FLExProject-level service/factory accessors) are listed in [Recent Additions (Post-v2.0)](#recent-additions-post-v20) at the end of this document. That section is grouped by Operations class rather than phase because the post-v2.0 work doesn't map onto the original phase model cleanly — e.g. Phonological Rules received new methods in Phase 5e *and* catalog plumbing in Phase 6, and the catalog imports themselves cut across four operations classes.

---

## Phase 1: Core Text & Lexicon Objects

### POSOperations

#### `project.POS.GetAll()`
**Replaces:** `ILangProject.PartsOfSpeechOA.PossibilitiesOS` iteration

#### `project.POS.Create(name, abbreviation, catalogSourceId=None)`
**Replaces:** `IPartOfSpeechFactory.Create()`, `IPartOfSpeech.Name.set_String()`, `IPartOfSpeech.Abbreviation.set_String()`, `ICmPossibilityList.PossibilitiesOS.Add()`

#### `project.POS.Delete(pos_or_hvo)`
**Replaces:** `ICmPossibilityList.PossibilitiesOS.Remove()`

#### `project.POS.Exists(name)`
**Replaces:** Manual iteration through `PartsOfSpeechOA.PossibilitiesOS` with name comparison

#### `project.POS.Find(name)`
**Replaces:** Recursive search through `IPartOfSpeech.SubPossibilitiesOS` collections

#### `project.POS.GetName(pos_or_hvo, wsHandle=None)`
**Replaces:** `IPartOfSpeech.Name.get_String()`, `ITsString.Text`

#### `project.POS.SetName(pos_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IPartOfSpeech.Name.set_String()`

#### `project.POS.GetAbbreviation(pos_or_hvo, wsHandle=None)`
**Replaces:** `IPartOfSpeech.Abbreviation.get_String()`, `ITsString.Text`

#### `project.POS.SetAbbreviation(pos_or_hvo, abbr, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IPartOfSpeech.Abbreviation.set_String()`

#### `project.POS.GetSubcategories(pos_or_hvo)`
**Replaces:** `IPartOfSpeech.SubPossibilitiesOS` list conversion

#### `project.POS.AddSubcategory(pos_or_hvo, name, abbreviation)`
**Replaces:** `IPartOfSpeechFactory.Create()`, `IPartOfSpeech.SubPossibilitiesOS.Add()`

#### `project.POS.RemoveSubcategory(pos_or_hvo, subcat_or_hvo)`
**Replaces:** `IPartOfSpeech.SubPossibilitiesOS.Remove()`

#### `project.POS.GetCatalogSourceId(pos_or_hvo)`
**Replaces:** `IPartOfSpeech.CatalogSourceId` property access

#### `project.POS.GetInflectionClasses(pos_or_hvo)`
**Replaces:** `IPartOfSpeech.InflectionClassesOC` list conversion

#### `project.POS.GetAffixSlots(pos_or_hvo)`
**Replaces:** `IPartOfSpeech.AffixSlotsOC` list conversion

#### `project.POS.GetEntryCount(pos_or_hvo)`
**Replaces:** `ILexEntryRepository.AllInstances()` iteration with morph type filtering


### TextOperations

#### `project.Texts.Create(name, genre=None)`
**Replaces:** `ITextFactory.Create()`, `IStTextFactory.Create()`, `ILangProject.TextsOC.Add()`, `IText.Name.set_String()`, `IText.ContentsOA` assignment

#### `project.Texts.Delete(text_or_hvo)`
**Replaces:** `ILangProject.TextsOC.Remove()`

#### `project.Texts.Exists(name)`
**Replaces:** `ITextRepository` iteration with name comparison

#### `project.Texts.GetAll()`
**Replaces:** `ITextRepository.AllInstances()` or `ObjectsIn(ITextRepository)`

#### `project.Texts.GetName(text_or_hvo, wsHandle=None)`
**Replaces:** `IText.Name.get_String()`, `ITsString.Text`

#### `project.Texts.SetName(text_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IText.Name.set_String()`

#### `project.Texts.GetGenre(text_or_hvo)`
**Replaces:** `IText.GenresRC.FirstOrDefault()`

#### `project.Texts.SetGenre(text_or_hvo, genre)`
**Replaces:** `IText.GenresRC.Clear()`, `IText.GenresRC.Add()`

#### `project.Texts.GetContents(text_or_hvo)`
**Replaces:** `IText.ContentsOA` property access

#### `project.Texts.GetParagraphs(text_or_hvo)`
**Replaces:** `IText.ContentsOA.ParagraphsOS` list conversion

#### `project.Texts.GetParagraphCount(text_or_hvo)`
**Replaces:** `IText.ContentsOA.ParagraphsOS.Count`

#### `project.Texts.GetMediaFiles(text_or_hvo)`
**Replaces:** `IText.MediaFilesOA.MediaFilesOC` list conversion

#### `project.Texts.AddMediaFile(text_or_hvo, filepath, label=None)`
**Replaces:** `ICmFolderFactory.Create()`, `ICmMediaFactory.Create()`, `MediaOperations.CopyToProject()`, `IText.MediaFilesOA.MediaFilesOC.Add()`

#### `project.Texts.GetAbbreviation(text_or_hvo, wsHandle=None)`
**Replaces:** `IText.Abbreviation.get_String()`, `ITsString.Text`


### WordformOperations

#### `project.Wordforms.GetAll()`
**Replaces:** `IWfiWordformRepository.AllInstances()` or `ObjectsIn(IWfiWordformRepository)`

#### `project.Wordforms.Create(form, wsHandle=None)`
**Replaces:** `IWfiWordformFactory.Create()`, `TsStringUtils.MakeString()`, `IWfiWordform.Form.set_String()`, `IWfiWordformInventory.WordformsOC.Add()`

#### `project.Wordforms.Delete(wordform_or_hvo)`
**Replaces:** `IWfiWordformInventory.WordformsOC.Remove()`

#### `project.Wordforms.Exists(form, wsHandle=None)`
**Replaces:** Manual search through `IWfiWordformRepository` with form comparison

#### `project.Wordforms.Find(form, wsHandle=None)`
**Replaces:** Iteration through `IWfiWordformRepository` with form matching

#### `project.Wordforms.GetForm(wordform_or_hvo, wsHandle=None)`
**Replaces:** `IWfiWordform.Form.get_String()`, `ITsString.Text`

#### `project.Wordforms.SetForm(wordform_or_hvo, form, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IWfiWordform.Form.set_String()`

#### `project.Wordforms.GetSpellingStatus(wordform_or_hvo)`
**Replaces:** `IWfiWordform.SpellingStatus` property access

#### `project.Wordforms.SetSpellingStatus(wordform_or_hvo, status)`
**Replaces:** `IWfiWordform.SpellingStatus` property assignment

#### `project.Wordforms.GetAnalyses(wordform_or_hvo)`
**Replaces:** `IWfiWordform.AnalysesOC` list conversion

#### `project.Wordforms.GetOccurrenceCount(wordform_or_hvo)`
**Replaces:** `IWfiWordform.OccurrencesRS.Count`

#### `project.Wordforms.GetOccurrences(wordform_or_hvo)`
**Replaces:** `IWfiWordform.OccurrencesRS` list conversion

#### `project.Wordforms.GetChecksum(wordform_or_hvo)`
**Replaces:** `IWfiWordform.Checksum` property access

#### `project.Wordforms.GetAllWithStatus(status)`
**Replaces:** Filtered iteration of `IWfiWordformRepository` by `SpellingStatus`

#### `project.Wordforms.GetAllUnapproved()`
**Replaces:** Filtered iteration excluding `SpellingStatus == CORRECT`

#### `project.Wordforms.ApproveSpelling(wordform_or_hvo)`
**Replaces:** `IWfiWordform.SpellingStatus = SpellingStatusStates.CORRECT`

---

## Phase 2: Lexical Entry Operations

### LexEntryOperations

#### `project.LexEntry.GetAll()`
**Replaces:** `ILexEntryRepository.AllInstances()` or `ObjectsIn(ILexEntryRepository)`

#### `project.LexEntry.Create(lexeme_form, morph_type_name="stem", wsHandle=None)`
**Replaces:** `ILexEntryFactory.Create()`, `IMoStemAllomorphFactory.Create()`, `TsStringUtils.MakeString()`, `IMoForm.Form.set_String()`, `IMoForm.MorphTypeRA` assignment, `ILexEntry.LexemeFormOA` assignment, `ILexDb.EntriesOC.Add()`

#### `project.LexEntry.Delete(entry_or_hvo)`
**Replaces:** `ILexDb.EntriesOC.Remove()`

#### `project.LexEntry.Exists(lexeme_form, wsHandle=None)`
**Replaces:** Manual search through `ILexEntryRepository` with lexeme form comparison

#### `project.LexEntry.Find(lexeme_form, wsHandle=None)`
**Replaces:** Iteration through `ILexEntryRepository` with `LexemeFormOA.Form` matching

#### `project.LexEntry.GetHeadword(entry_or_hvo)`
**Replaces:** `ILexEntry.HeadWord.Text` property access

#### `project.LexEntry.SetHeadword(entry_or_hvo, text, wsHandle=None)`
**Replaces:** Calls `SetLexemeForm()` (wrapper method)

#### `project.LexEntry.GetLexemeForm(entry_or_hvo, wsHandle=None)`
**Replaces:** `ILexEntry.LexemeFormOA.Form.get_String()`, `ITsString.Text`

#### `project.LexEntry.SetLexemeForm(entry_or_hvo, text, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ILexEntry.LexemeFormOA.Form.set_String()`

#### `project.LexEntry.GetCitationForm(entry_or_hvo, wsHandle=None)`
**Replaces:** `ILexEntry.CitationForm.get_String()`, `ITsString.Text`

#### `project.LexEntry.SetCitationForm(entry_or_hvo, text, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ILexEntry.CitationForm.set_String()`

#### `project.LexEntry.GetHomographNumber(entry_or_hvo)`
**Replaces:** `ILexEntry.HomographNumber` property access

#### `project.LexEntry.SetHomographNumber(entry_or_hvo, number)`
**Replaces:** `ILexEntry.HomographNumber` property assignment

#### `project.LexEntry.GetDateCreated(entry_or_hvo)`
**Replaces:** `ILexEntry.DateCreated` property access

#### `project.LexEntry.GetDateModified(entry_or_hvo)`
**Replaces:** `ILexEntry.DateModified` property access

#### `project.LexEntry.GetMorphType(entry_or_hvo)`
**Replaces:** `ILexEntry.LexemeFormOA.MorphTypeRA` property access

#### `project.LexEntry.SetMorphType(entry_or_hvo, morph_type_or_name)`
**Replaces:** `IMoStemMsaFactory.Create()`, `IMoMorphType` lookup, `ILexEntry.LexemeFormOA.MorphTypeRA` assignment

#### `project.LexEntry.GetSenses(entry_or_hvo)`
**Replaces:** `ILexEntry.SensesOS` list conversion

#### `project.LexEntry.GetSenseCount(entry_or_hvo)`
**Replaces:** `ILexEntry.SensesOS.Count`

#### `project.LexEntry.AddSense(entry_or_hvo, gloss, wsHandle=None)`
**Replaces:** `ILexSenseFactory.Create()`, `TsStringUtils.MakeString()`, `ILexSense.Gloss.set_String()`, `ILexEntry.SensesOS.Add()`

#### `project.LexEntry.GetGuid(entry_or_hvo)`
**Replaces:** `ILexEntry.Guid` property access

#### `project.LexEntry.GetImportResidue(entry_or_hvo)`
**Replaces:** `ILexEntry.ImportResidue` property access

#### `project.LexEntry.SetImportResidue(entry_or_hvo, residue)`
**Replaces:** `ILexEntry.ImportResidue` property assignment

---

## Phase 3: Reversal Index Operations

> **REMOVED in v3.0**: The bundled `project.Reversal` API has been removed.
> Use the modular APIs instead:
> - `project.ReversalIndexes` - for index-level operations
> - `project.ReversalEntries` - for entry-level operations

---

## Phase 4: Writing System Operations

### WritingSystemOperations

#### `project.WritingSystems.GetAll()`
**Replaces:** `WritingSystemManager.AllWritingSystems` filtered by active WS tags

#### `project.WritingSystems.GetVernacular()`
**Replaces:** `WritingSystemManager.AllWritingSystems` filtered by `CurVernWss`

#### `project.WritingSystems.GetAnalysis()`
**Replaces:** `WritingSystemManager.AllWritingSystems` filtered by `CurAnalysisWss`

#### `project.WritingSystems.Create(language_tag, name, is_vernacular=True)`
**Replaces:** `WritingSystemManager.Create()`, `IWritingSystemDefinition` property assignments, `ILangProject.CurVernWss/CurAnalysisWss` updates

#### `project.WritingSystems.Delete(ws_handle_or_tag)`
**Replaces:** WS removal from `CurVernWss/CurAnalysisWss` string lists

#### `project.WritingSystems.GetFontName(ws)`
**Replaces:** `IWritingSystemDefinition.DefaultFontName` or `DefaultFont` property access

#### `project.WritingSystems.SetFontName(ws, font_name)`
**Replaces:** `IWritingSystemDefinition.DefaultFontName` or `DefaultFont` property assignment

#### `project.WritingSystems.GetFontSize(ws)`
**Replaces:** `IWritingSystemDefinition.DefaultFontSize` property access

#### `project.WritingSystems.SetFontSize(ws, size)`
**Replaces:** `IWritingSystemDefinition.DefaultFontSize` property assignment

#### `project.WritingSystems.GetRightToLeft(ws)`
**Replaces:** `IWritingSystemDefinition.RightToLeftScript` or `RightToLeft` property access

#### `project.WritingSystems.SetRightToLeft(ws, is_rtl)`
**Replaces:** `IWritingSystemDefinition.RightToLeftScript` or `RightToLeft` property assignment

#### `project.WritingSystems.SetDefaultVernacular(ws)`
**Replaces:** `ILangProject.DefaultVernacularWritingSystem` property assignment

#### `project.WritingSystems.SetDefaultAnalysis(ws)`
**Replaces:** `ILangProject.DefaultAnalysisWritingSystem` property assignment

#### `project.WritingSystems.GetDefaultVernacular()`
**Replaces:** `ILangProject.DefaultVernacularWritingSystem` property access

#### `project.WritingSystems.GetDefaultAnalysis()`
**Replaces:** `ILangProject.DefaultAnalysisWritingSystem` property access

#### `project.WritingSystems.GetDisplayName(ws)`
**Replaces:** `IWritingSystemDefinition.DisplayLabel` or `Id` property access

#### `project.WritingSystems.GetLanguageTag(ws)`
**Replaces:** `IWritingSystemDefinition.Id` property access

#### `project.WritingSystems.Exists(language_tag)`
**Replaces:** Search through `WritingSystemManager.AllWritingSystems` by `Id`

---

## Phase 5: Morphology Type & Rule Operations

### MorphRuleOperations

*(Based on file pattern from codebase - not fully read)*

Methods for managing morphological rules including:
- Create/Delete rules
- Get/Set rule properties
- Manage rule environments
- Handle rule stratum assignments

**Note:** Detailed method signatures require reading MorphRuleOperations.py file.

---

## Phase 6: Example Sentences & Pictures

### ExampleOperations

#### `project.Examples.GetAll(sense_or_hvo)`
**Replaces:** `ILexSense.ExamplesOS` iteration

#### `project.Examples.Create(sense_or_hvo, example_text, wsHandle=None)`
**Replaces:** `ILexExampleSentenceFactory.Create()`, `TsStringUtils.MakeString()`, `ILexExampleSentence.Example.set_String()`, `ILexSense.ExamplesOS.Add()`

#### `project.Examples.Delete(example_or_hvo)`
**Replaces:** `ILexSense.ExamplesOS.Remove()`

#### `project.Examples.Reorder(sense_or_hvo, example_list)`
**Replaces:** `ILexSense.ExamplesOS.Clear()`, `ILexSense.ExamplesOS.Add()` in sequence

#### `project.Examples.GetExample(example_or_hvo, wsHandle=None)`
**Replaces:** `ILexExampleSentence.Example.get_String()`, `ITsString.Text`

#### `project.Examples.SetExample(example_or_hvo, text, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ILexExampleSentence.Example.set_String()`

#### `project.Examples.GetTranslations(example_or_hvo)`
**Replaces:** `ILexExampleSentence.TranslationsOC` list conversion

#### `project.Examples.GetTranslation(example_or_hvo, wsHandle=None)`
**Replaces:** Iteration through `TranslationsOC` with WS matching on `ICmTranslation.Translation.get_String()`

#### `project.Examples.SetTranslation(example_or_hvo, text, wsHandle=None)`
**Replaces:** `ICmTranslationFactory.Create()`, `TsStringUtils.MakeString()`, `ICmTranslation.Translation.set_String()`, `ILexExampleSentence.TranslationsOC.Add()`

#### `project.Examples.AddTranslation(example_or_hvo, text, wsHandle=None)`
**Replaces:** Alias for `SetTranslation()` - same LibLCM calls

#### `project.Examples.RemoveTranslation(example_or_hvo, wsHandle=None)`
**Replaces:** `ICmTranslation.Translation.set_String(None)` to clear

#### `project.Examples.GetReference(example_or_hvo)`
**Replaces:** `ILexExampleSentence.Reference`, `ITsString.Text`

#### `project.Examples.SetReference(example_or_hvo, reference_text)`
**Replaces:** `TsStringUtils.MakeString()`, `ILexExampleSentence.Reference` assignment

#### `project.Examples.GetMediaFiles(example_or_hvo)`
**Replaces:** `ILexExampleSentence.MediaFilesOS` list conversion

#### `project.Examples.GetMediaCount(example_or_hvo)`
**Replaces:** `ILexExampleSentence.MediaFilesOS.Count`

#### `project.Examples.GetOwningSense(example_or_hvo)`
**Replaces:** `ILexExampleSentence.Owner` property access

#### `project.Examples.GetGuid(example_or_hvo)`
**Replaces:** `ILexExampleSentence.Guid` property access

### PictureOperations

*(Based on file pattern from codebase - not fully read)*

Methods for managing pictures on lexical senses including:
- Add/Remove pictures
- Get/Set captions
- Manage picture files

---

## Phase 7: Lexical Sense Operations

### LexSenseOperations

#### `project.Senses.GetAll(entry_or_hvo)`
**Replaces:** `ILexEntry.SensesOS` iteration

#### `project.Senses.Create(entry_or_hvo, gloss, wsHandle=None)`
**Replaces:** `ILexSenseFactory.Create()`, `TsStringUtils.MakeString()`, `ILexSense.Gloss.set_String()`, `ILexEntry.SensesOS.Add()`

#### `project.Senses.Delete(sense_or_hvo)`
**Replaces:** `ILexEntry.SensesOS.Remove()` or `ILexSense.SensesOS.Remove()` for subsenses

#### `project.Senses.Reorder(entry_or_hvo, sense_list)`
**Replaces:** `ILexEntry.SensesOS.Clear()`, `ILexEntry.SensesOS.Add()` in sequence

#### `project.Senses.GetGloss(sense_or_hvo, wsHandle=None)`
**Replaces:** `ILexSense.Gloss.get_String()`, `ITsString.Text`

#### `project.Senses.SetGloss(sense_or_hvo, text, wsHandle=None)`
**Replaces:** `ILexSense.Gloss.set_String()` (handles TsString creation internally)

#### `project.Senses.GetDefinition(sense_or_hvo, wsHandle=None)`
**Replaces:** `ILexSense.Definition.get_String()`, `ITsString.Text`

#### `project.Senses.SetDefinition(sense_or_hvo, text, wsHandle=None)`
**Replaces:** `ILexSense.Definition.set_String()`

#### `project.Senses.GetPartOfSpeech(sense_or_hvo)`
**Replaces:** `ILexSense.MorphoSyntaxAnalysisRA.InterlinearAbbr`

#### `project.Senses.SetPartOfSpeech(sense_or_hvo, pos)`
**Replaces:** `IMoStemMsaFactory.Create()`, `IMoMorphSynAnalysis.PartOfSpeechRA` assignment, `ILexSense.MorphoSyntaxAnalysisRA` assignment

#### `project.Senses.GetGrammaticalInfo(sense_or_hvo)`
**Replaces:** `ILexSense.MorphoSyntaxAnalysisRA` property access

#### `project.Senses.SetGrammaticalInfo(sense_or_hvo, msa)`
**Replaces:** `ILexSense.MorphoSyntaxAnalysisRA` property assignment

#### `project.Senses.GetSemanticDomains(sense_or_hvo)`
**Replaces:** `ILexSense.SemanticDomainsRC` list conversion

#### `project.Senses.AddSemanticDomain(sense_or_hvo, domain_or_hvo)`
**Replaces:** `ILexSense.SemanticDomainsRC.Add()`

#### `project.Senses.RemoveSemanticDomain(sense_or_hvo, domain_or_hvo)`
**Replaces:** `ILexSense.SemanticDomainsRC.Remove()`

#### `project.Senses.GetExamples(sense_or_hvo)`
**Replaces:** `ILexSense.ExamplesOS` list conversion

#### `project.Senses.GetExampleCount(sense_or_hvo)`
**Replaces:** `ILexSense.ExamplesOS.Count`

#### `project.Senses.AddExample(sense_or_hvo, text, wsHandle=None)`
**Replaces:** `ILexExampleSentenceFactory.Create()`, `TsStringUtils.MakeString()`, `ILexExampleSentence.Example.set_String()`, `ILexSense.ExamplesOS.Add()`

#### `project.Senses.GetSubsenses(sense_or_hvo)`
**Replaces:** `ILexSense.SensesOS` list conversion

#### `project.Senses.CreateSubsense(parent_sense_or_hvo, gloss, wsHandle=None)`
**Replaces:** `ILexSenseFactory.Create()`, `TsStringUtils.MakeString()`, `ILexSense.Gloss.set_String()`, `ILexSense.SensesOS.Add()`

#### `project.Senses.GetParentSense(sense_or_hvo)`
**Replaces:** `ILexSense.Owner` property access with type checking

#### `project.Senses.GetStatus(sense_or_hvo)`
**Replaces:** `ILexSense.StatusRA` property access

#### `project.Senses.SetStatus(sense_or_hvo, status)`
**Replaces:** `ILexSense.StatusRA` property assignment

#### `project.Senses.GetSenseType(sense_or_hvo)`
**Replaces:** `ILexSense.SenseTypeRA` property access

#### `project.Senses.SetSenseType(sense_or_hvo, sense_type)`
**Replaces:** `ILexSense.SenseTypeRA` property assignment

#### `project.Senses.GetReversalEntries(sense_or_hvo, reversal_index_ws=None)`
**Replaces:** `ILexSense.ReferringReversalIndexEntries` list conversion with optional filtering

#### `project.Senses.GetReversalCount(sense_or_hvo)`
**Replaces:** `ILexSense.ReferringReversalIndexEntries` count

#### `project.Senses.GetPictures(sense_or_hvo)`
**Replaces:** `ILexSense.PicturesOS` list conversion

#### `project.Senses.GetPictureCount(sense_or_hvo)`
**Replaces:** `ILexSense.PicturesOS.Count`

#### `project.Senses.GetGuid(sense_or_hvo)`
**Replaces:** `ILexSense.Guid` property access

#### `project.Senses.GetOwningEntry(sense_or_hvo)`
**Replaces:** Climbing `ILexSense.Owner` chain to find `ILexEntry`

#### `project.Senses.GetSenseNumber(sense_or_hvo)`
**Replaces:** `ReflectionHelper.GetProperty(sense, "SenseNumber")`

#### `project.Senses.GetAnalysesCount(sense_or_hvo)`
**Replaces:** `ReflectionHelper.GetProperty(sense, "SenseAnalysesCount")`

---

## Phase 8: Pronunciations, Variants & Allomorphs

### PronunciationOperations

#### `project.Pronunciations.GetAll(entry_or_hvo)`
**Replaces:** `ILexEntry.PronunciationsOS` iteration

#### `project.Pronunciations.Create(entry_or_hvo, form, wsHandle=None)`
**Replaces:** `ILexPronunciationFactory.Create()`, `TsStringUtils.MakeString()`, `ILexPronunciation.Form.set_String()`, `ILexEntry.PronunciationsOS.Add()`

#### `project.Pronunciations.Delete(pronunciation_or_hvo)`
**Replaces:** `ILexEntry.PronunciationsOS.Remove()`

#### `project.Pronunciations.Reorder(entry_or_hvo, pronunciation_list)`
**Replaces:** `ILexEntry.PronunciationsOS.Clear()`, `ILexEntry.PronunciationsOS.Add()` in sequence

#### `project.Pronunciations.GetForm(pronunciation_or_hvo, wsHandle=None)`
**Replaces:** `ILexPronunciation.Form.get_String()`, `ITsString.Text`

#### `project.Pronunciations.SetForm(pronunciation_or_hvo, text, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ILexPronunciation.Form.set_String()`

#### `project.Pronunciations.GetMediaFiles(pronunciation_or_hvo)`
**Replaces:** `ILexPronunciation.MediaFilesOS` list conversion

#### `project.Pronunciations.GetMediaCount(pronunciation_or_hvo)`
**Replaces:** `ILexPronunciation.MediaFilesOS.Count`

#### `project.Pronunciations.AddMediaFile(pronunciation_or_hvo, file_path, label=None)`
**Replaces:** `MediaOperations.CopyToProject()`, `ILexPronunciation.MediaFilesOS.Add()`

#### `project.Pronunciations.RemoveMediaFile(pronunciation_or_hvo, media_or_hvo)`
**Replaces:** `ILexPronunciation.MediaFilesOS.Remove()`

#### `project.Pronunciations.GetLocation(pronunciation_or_hvo)`
**Replaces:** `ILexPronunciation.LocationRA` property access

#### `project.Pronunciations.SetLocation(pronunciation_or_hvo, location)`
**Replaces:** `ILexPronunciation.LocationRA` property assignment

#### `project.Pronunciations.GetOwningEntry(pronunciation_or_hvo)`
**Replaces:** `ILexPronunciation.Owner` property access

#### `project.Pronunciations.GetGuid(pronunciation_or_hvo)`
**Replaces:** `ILexPronunciation.Guid` property access

### VariantOperations

*(Methods for managing variant forms and relationships - file not fully read)*

### AllomorphOperations

*(Methods for managing allomorphs of entries - file not fully read)*

---

## Phase 9: WfiAnalysis, Filters & Discourse

### WfiAnalysisOperations

Methods for managing wordform analyses in texts:

#### `project.WfiAnalysis.GetAll(wordform_or_hvo)`
**Replaces:** `IWfiWordform.AnalysesOC` iteration

#### `project.WfiAnalysis.Create(wordform_or_hvo)`
**Replaces:** `IWfiAnalysisFactory.Create()`, `IWfiWordform.AnalysesOC.Add()`

#### `project.WfiAnalysis.Delete(analysis_or_hvo)`
**Replaces:** `IWfiWordform.AnalysesOC.Remove()`

#### `project.WfiAnalysis.GetMorphBundles(analysis_or_hvo)`
**Replaces:** `IWfiAnalysis.MorphBundlesOS` list conversion

#### `project.WfiAnalysis.AddMorphBundle(analysis_or_hvo)`
**Replaces:** `IWfiMorphBundleFactory.Create()`, `IWfiAnalysis.MorphBundlesOS.Add()`

#### `project.WfiAnalysis.GetCategory(analysis_or_hvo)`
**Replaces:** `IWfiAnalysis.CategoryRA` property access

#### `project.WfiAnalysis.SetCategory(analysis_or_hvo, category)`
**Replaces:** `IWfiAnalysis.CategoryRA` property assignment

#### `project.WfiAnalysis.Approve(analysis_or_hvo)`
**Replaces:** `IWfiAnalysis` evaluation status update

### FilterOperations

Methods for managing record filters:

#### `project.Filters.GetAll()`
**Replaces:** `ICmFilterRepository.AllInstances()` iteration

#### `project.Filters.Create(name, app_type)`
**Replaces:** `ICmFilterFactory.Create()`, filter configuration

#### `project.Filters.Delete(filter_or_hvo)`
**Replaces:** Repository-based filter removal

#### `project.Filters.GetName(filter_or_hvo, wsHandle=None)`
**Replaces:** `ICmFilter.Name.get_String()`, `ITsString.Text`

#### `project.Filters.SetName(filter_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmFilter.Name.set_String()`

### DiscourseOperations

Methods for discourse chart analysis:

#### `project.Discourse.GetAllCharts()`
**Replaces:** `IDsConstChartRepository.AllInstances()` or chart collection iteration

#### `project.Discourse.CreateChart(name, text)`
**Replaces:** `IDsConstChartFactory.Create()`, chart template setup

#### `project.Discourse.DeleteChart(chart_or_hvo)`
**Replaces:** Chart repository removal

#### `project.Discourse.GetRows(chart_or_hvo)`
**Replaces:** `IConstChart.RowsOS` iteration

#### `project.Discourse.AddRow(chart_or_hvo)`
**Replaces:** `IConstChartRowFactory.Create()`, `IConstChart.RowsOS.Add()`

---

## Phase 10: Variant Forms & Discourse

### VariantOperations

Methods for managing lexical entry variants:

#### `project.Variants.GetAll(entry_or_hvo)`
**Replaces:** `ILexEntry.VariantEntryTypesOS` or variant reference iteration

#### `project.Variants.Create(entry_or_hvo, variant_form, variant_type)`
**Replaces:** `ILexEntryFactory.Create()`, `ILexEntryRef.VariantEntryTypesRS.Add()`, variant linkage setup

#### `project.Variants.Delete(variant_or_hvo)`
**Replaces:** Variant entry deletion and reference cleanup

#### `project.Variants.GetVariantType(variant_or_hvo)`
**Replaces:** `ILexEntryRef.VariantEntryTypesRS` access

#### `project.Variants.SetVariantType(variant_or_hvo, variant_type)`
**Replaces:** `ILexEntryRef.VariantEntryTypesRS` modification

#### `project.Variants.GetComponentEntries(variant_or_hvo)`
**Replaces:** `ILexEntryRef.ComponentLexemesRS` list conversion

#### `project.Variants.AddComponentEntry(variant_or_hvo, entry)`
**Replaces:** `ILexEntryRef.ComponentLexemesRS.Add()`

---

## Phase 11: Allomorphs, Media, Persons & Agents

### AllomorphOperations

Methods for managing entry allomorphs:

#### `project.Allomorphs.GetAll(entry_or_hvo)`
**Replaces:** `ILexEntry.AlternateFormsOS` iteration

#### `project.Allomorphs.Create(entry_or_hvo, form, morph_type, wsHandle=None)`
**Replaces:** `IMoStemAllomorphFactory.Create()` or `IMoAffixAllomorphFactory.Create()`, `ILexEntry.AlternateFormsOS.Add()`

#### `project.Allomorphs.Delete(allomorph_or_hvo)`
**Replaces:** `ILexEntry.AlternateFormsOS.Remove()`

#### `project.Allomorphs.GetForm(allomorph_or_hvo, wsHandle=None)`
**Replaces:** `IMoForm.Form.get_String()`, `ITsString.Text`

#### `project.Allomorphs.SetForm(allomorph_or_hvo, form, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IMoForm.Form.set_String()`

#### `project.Allomorphs.GetMorphType(allomorph_or_hvo)`
**Replaces:** `IMoForm.MorphTypeRA` property access

#### `project.Allomorphs.SetMorphType(allomorph_or_hvo, morph_type)`
**Replaces:** `IMoForm.MorphTypeRA` property assignment

### MediaOperations

Methods for managing media files:

#### `project.Media.GetAll()`
**Replaces:** `ICmMediaRepository.AllInstances()` or media folder iteration

#### `project.Media.Create(filepath, label=None)`
**Replaces:** `ICmMediaFactory.Create()`, file copy operations, `ICmFolder.FilesOC.Add()`

#### `project.Media.Delete(media_or_hvo)`
**Replaces:** `ICmFolder.FilesOC.Remove()`, file cleanup

#### `project.Media.Find(filename)`
**Replaces:** Media repository search by filename

#### `project.Media.GetInternalPath(media_or_hvo)`
**Replaces:** `ICmMedia.InternalPath` or `ICmFile.InternalPath` property access

#### `project.Media.GetLabel(media_or_hvo, wsHandle=None)`
**Replaces:** `ICmMedia.Label.get_String()`, `ITsString.Text`

#### `project.Media.SetLabel(media_or_hvo, label, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmMedia.Label.set_String()`

### PersonOperations

Methods for managing person records:

#### `project.Person.GetAll()`
**Replaces:** `ICmPersonRepository.AllInstances()` iteration

#### `project.Person.Create(name, wsHandle=None)`
**Replaces:** `ICmPersonFactory.Create()`, `ICmPerson.Name.set_String()`, `ILangProject.PeopleOA.PossibilitiesOS.Add()`

#### `project.Person.Delete(person_or_hvo)`
**Replaces:** `ILangProject.PeopleOA.PossibilitiesOS.Remove()`

#### `project.Person.Find(name, wsHandle=None)`
**Replaces:** Person repository search by name

#### `project.Person.Exists(name, wsHandle=None)`
**Replaces:** Person existence check via search

#### `project.Person.GetName(person_or_hvo, wsHandle=None)`
**Replaces:** `ICmPerson.Name.get_String()`, `ITsString.Text`

#### `project.Person.SetName(person_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmPerson.Name.set_String()`

### AgentOperations

Methods for managing analyst agents:

#### `project.Agents.GetAll()`
**Replaces:** `ICmAgentRepository.AllInstances()` iteration

#### `project.Agents.Create(name, wsHandle=None)`
**Replaces:** `ICmAgentFactory.Create()`, `ICmAgent.Name.set_String()`, `ILangProject.AnalyzingAgentsOC.Add()`

#### `project.Agents.Delete(agent_or_hvo)`
**Replaces:** `ILangProject.AnalyzingAgentsOC.Remove()`

#### `project.Agents.Find(name, wsHandle=None)`
**Replaces:** Agent repository search by name

#### `project.Agents.Exists(name, wsHandle=None)`
**Replaces:** Agent existence check via search

#### `project.Agents.GetName(agent_or_hvo, wsHandle=None)`
**Replaces:** `ICmAgent.Name.get_String()`, `ITsString.Text`

#### `project.Agents.SetName(agent_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmAgent.Name.set_String()`

#### `project.Agents.GetVersion(agent_or_hvo, wsHandle=None)`
**Replaces:** `ICmAgent.Version.get_String()`, `ITsString.Text`

#### `project.Agents.SetVersion(agent_or_hvo, version, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmAgent.Version.set_String()`

#### `project.Agents.IsHuman(agent_or_hvo)`
**Replaces:** `ICmAgent.Human` property null check

#### `project.Agents.IsParser(agent_or_hvo)`
**Replaces:** `ICmAgent.Human` property null check (inverted logic)

#### `project.Agents.GetHuman(agent_or_hvo)`
**Replaces:** `ICmAgent.Human` property access (returns `ICmPerson`)

#### `project.Agents.SetHuman(agent_or_hvo, person)`
**Replaces:** `ICmAgent.Human` property assignment

#### `project.Agents.GetApprovals(agent_or_hvo)`
**Replaces:** `ICmAgent.ApprovalsOS` list conversion

#### `project.Agents.GetEvaluations(agent_or_hvo)`
**Replaces:** `ICmAgent.EvaluationsRC` list conversion

#### `project.Agents.CreateHumanAgent(name, person, wsHandle=None)`
**Replaces:** `Create()` + `SetHuman()` combined operation

#### `project.Agents.CreateParserAgent(name, version, wsHandle=None)`
**Replaces:** `Create()` + `SetVersion()` combined operation

---

## Phase 12: Translation Types, Semantic Domains & Possibility Lists

### TranslationTypeOperations

Methods for managing translation type classifications:

#### `project.TranslationType.GetAll()`
**Replaces:** `ILangProject.TranslationTagsOA.PossibilitiesOS` iteration

#### `project.TranslationType.Create(name, abbreviation=None)`
**Replaces:** `ICmPossibilityFactory.Create()`, `ILangProject.TranslationTagsOA.PossibilitiesOS.Add()`

#### `project.TranslationType.Delete(type_or_hvo)`
**Replaces:** `ILangProject.TranslationTagsOA.PossibilitiesOS.Remove()`

#### `project.TranslationType.Find(name, wsHandle=None)`
**Replaces:** Translation type search by name

#### `project.TranslationType.GetName(type_or_hvo, wsHandle=None)`
**Replaces:** `ICmPossibility.Name.get_String()`, `ITsString.Text`

#### `project.TranslationType.SetName(type_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmPossibility.Name.set_String()`

### SemanticDomainOperations

Methods for managing semantic domain hierarchies:

#### `project.SemanticDomain.GetAll()`
**Replaces:** `ILangProject.SemanticDomainListOA.PossibilitiesOS` recursive iteration

#### `project.SemanticDomain.Create(name, parent=None)`
**Replaces:** `ICmSemanticDomainFactory.Create()`, `ICmSemanticDomain.Name.set_String()`, parent/list `PossibilitiesOS.Add()`

#### `project.SemanticDomain.Delete(domain_or_hvo)`
**Replaces:** `PossibilitiesOS.Remove()` from parent or list

#### `project.SemanticDomain.Find(name_or_abbr, wsHandle=None)`
**Replaces:** Recursive semantic domain search by name or abbreviation

#### `project.SemanticDomain.GetName(domain_or_hvo, wsHandle=None)`
**Replaces:** `ICmSemanticDomain.Name.get_String()`, `ITsString.Text`

#### `project.SemanticDomain.SetName(domain_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmSemanticDomain.Name.set_String()`

#### `project.SemanticDomain.GetAbbreviation(domain_or_hvo, wsHandle=None)`
**Replaces:** `ICmSemanticDomain.Abbreviation.get_String()`, `ITsString.Text`

#### `project.SemanticDomain.SetAbbreviation(domain_or_hvo, abbr, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmSemanticDomain.Abbreviation.set_String()`

#### `project.SemanticDomain.GetSubdomains(domain_or_hvo)`
**Replaces:** `ICmSemanticDomain.SubPossibilitiesOS` list conversion

#### `project.SemanticDomain.AddSubdomain(domain_or_hvo, name)`
**Replaces:** `ICmSemanticDomainFactory.Create()`, `SubPossibilitiesOS.Add()`

### PossibilityListOperations

Methods for managing generic possibility lists:

#### `project.PossibilityList.GetAll()`
**Replaces:** `ICmPossibilityListRepository.AllInstances()` iteration

#### `project.PossibilityList.GetList(list_name)`
**Replaces:** Possibility list search by name in repository

#### `project.PossibilityList.GetPossibilities(list_or_hvo)`
**Replaces:** `ICmPossibilityList.PossibilitiesOS` list conversion

#### `project.PossibilityList.CreatePossibility(list_or_hvo, name)`
**Replaces:** `ICmPossibilityFactory.Create()`, `ICmPossibilityList.PossibilitiesOS.Add()`

#### `project.PossibilityList.DeletePossibility(possibility_or_hvo)`
**Replaces:** `ICmPossibilityList.PossibilitiesOS.Remove()`

#### `project.PossibilityList.FindPossibility(list_or_hvo, name)`
**Replaces:** Possibility search by name in list

#### `project.PossibilityList.GetName(list_or_hvo, wsHandle=None)`
**Replaces:** `ICmPossibilityList.Name.get_String()`, `ITsString.Text`

---

## Phase 13: Checks, Overlays, Settings & Phonological Rules

### CheckOperations

Methods for data consistency checks:

#### `project.Checks.GetAllCheckTypes()`
**Replaces:** `ILangProject.ChecksOA.PossibilitiesOS` iteration

#### `project.Checks.CreateCheckType(name, description=None)`
**Replaces:** `ICmPossibilityFactory.Create()`, `ILangProject.ChecksOA.PossibilitiesOS.Add()`

#### `project.Checks.DeleteCheckType(check_type_or_hvo)`
**Replaces:** `ILangProject.ChecksOA.PossibilitiesOS.Remove()`

#### `project.Checks.FindCheckType(name, wsHandle=None)`
**Replaces:** Check type search by name

#### `project.Checks.GetName(check_type_or_hvo, wsHandle=None)`
**Replaces:** `ICmPossibility.Name.get_String()`, `ITsString.Text`

#### `project.Checks.SetName(check_type_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmPossibility.Name.set_String()`

#### `project.Checks.GetDescription(check_type_or_hvo, wsHandle=None)`
**Replaces:** `ICmPossibility.Description.get_String()`, `ITsString.Text`

#### `project.Checks.SetDescription(check_type_or_hvo, description, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmPossibility.Description.set_String()`

#### `project.Checks.RunCheck(check_type, scope=None)`
**Replaces:** Custom validation logic with LibLCM object iteration

#### `project.Checks.GetCheckResults(check_type)`
**Replaces:** Check result collection access

### OverlayOperations

Methods for discourse chart overlay management:

#### `project.Overlay.GetAll(chart_or_hvo)`
**Replaces:** `IConstChart.TemplateRA.ColumnsPossibilitiesOC` iteration

#### `project.Overlay.Create(chart_or_hvo, name, wsHandle=None)`
**Replaces:** `ICmPossibilityFactory.Create()`, `ICmPossibility.Name.set_String()`, `ColumnsPossibilitiesOC.Add()`

#### `project.Overlay.Delete(overlay_or_hvo)`
**Replaces:** `IConstChart.TemplateRA.ColumnsPossibilitiesOC.Remove()`

#### `project.Overlay.Find(chart_or_hvo, name, wsHandle=None)`
**Replaces:** Overlay search by name in chart template

#### `project.Overlay.GetName(overlay_or_hvo, wsHandle=None)`
**Replaces:** `ICmPossibility.Name.get_String()`, `ITsString.Text`

#### `project.Overlay.SetName(overlay_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ICmPossibility.Name.set_String()`

#### `project.Overlay.IsVisible(overlay_or_hvo)`
**Replaces:** `ICmPossibility.Hidden` property access (inverted logic)

#### `project.Overlay.SetVisible(overlay_or_hvo, visible)`
**Replaces:** `ICmPossibility.Hidden` property assignment (inverted)

#### `project.Overlay.GetDisplayOrder(overlay_or_hvo)`
**Replaces:** `ICmPossibility.SortSpec` or collection position access

#### `project.Overlay.SetDisplayOrder(overlay_or_hvo, order)`
**Replaces:** `ICmPossibility.SortSpec` assignment or collection reordering

#### `project.Overlay.GetElements(overlay_or_hvo)`
**Replaces:** Overlay cell/marker collection iteration

#### `project.Overlay.AddElement(overlay_or_hvo, element)`
**Replaces:** Chart cell or marker collection `Add()`

#### `project.Overlay.RemoveElement(overlay_or_hvo, element)`
**Replaces:** Chart cell or marker collection `Remove()`

#### `project.Overlay.GetChart(overlay_or_hvo)`
**Replaces:** Navigate ownership chain via `Owner` property to `IConstChart`

#### `project.Overlay.GetVisibleOverlays(chart_or_hvo)`
**Replaces:** Filtered iteration of overlays by `Hidden` property

### ProjectSettingsOperations

Methods for project configuration and settings:

#### `project.ProjectSettings.GetProjectName()`
**Replaces:** `ILangProject.Name` property access via `ITsString.Text`

#### `project.ProjectSettings.SetProjectName(name)`
**Replaces:** `TsStringUtils.MakeString()`, `ILangProject.Name` property assignment

#### `project.ProjectSettings.GetDescription(wsHandle=None)`
**Replaces:** `ILangProject.Description.get_String()`, `ITsString.Text`

#### `project.ProjectSettings.SetDescription(description, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `ILangProject.Description.set_String()`

#### `project.ProjectSettings.GetVernacularWSs()`
**Replaces:** `ILangProject.CurVernWss.split()` (space-separated list)

#### `project.ProjectSettings.GetAnalysisWSs()`
**Replaces:** `ILangProject.CurAnalysisWss.split()` (space-separated list)

#### `project.ProjectSettings.SetDefaultVernacular(ws_handle_or_tag)`
**Replaces:** `ILangProject.DefaultVernacularWritingSystem` property assignment

#### `project.ProjectSettings.SetDefaultAnalysis(ws_handle_or_tag)`
**Replaces:** `ILangProject.DefaultAnalysisWritingSystem` property assignment

#### `project.ProjectSettings.GetInterfaceLanguage()`
**Replaces:** `ILangProject.UserWs` property access

#### `project.ProjectSettings.SetInterfaceLanguage(ws_handle_or_tag)`
**Replaces:** `ILangProject.UserWs` property assignment

#### `project.ProjectSettings.GetDefaultFont(ws_handle_or_tag)`
**Replaces:** `IWritingSystemDefinition.DefaultFontName` property access

#### `project.ProjectSettings.SetDefaultFont(ws_handle_or_tag, font_name)`
**Replaces:** `IWritingSystemDefinition.DefaultFontName` property assignment

#### `project.ProjectSettings.GetDefaultFontSize(ws_handle_or_tag)`
**Replaces:** `IWritingSystemDefinition.DefaultFontSize` property access (float)

#### `project.ProjectSettings.SetDefaultFontSize(ws_handle_or_tag, size)`
**Replaces:** `IWritingSystemDefinition.DefaultFontSize` property assignment (float)

#### `project.ProjectSettings.GetLinkedFilesRootDir()`
**Replaces:** `ILangProject.LinkedFilesRootDir` property access

#### `project.ProjectSettings.SetLinkedFilesRootDir(path)`
**Replaces:** `ILangProject.LinkedFilesRootDir` property assignment

#### `project.ProjectSettings.GetExtLinkRootDir()`
**Replaces:** `ILangProject.ExtLinkRootDir` property access

#### `project.ProjectSettings.GetDateCreated()`
**Replaces:** `ILangProject.DateCreated` property access

#### `project.ProjectSettings.GetDateModified()`
**Replaces:** `ILangProject.DateModified` property access

### PhonologicalRuleOperations

Methods for phonological rule management:

#### `project.PhonologicalRule.GetAll()`
**Replaces:** `ILangProject.PhonologicalDataOA.PhonRulesOS` iteration

#### `project.PhonologicalRule.Create(name, description=None, wsHandle=None)`
**Replaces:** `IPhPhonRuleFactory.Create()`, `IPhPhonRule.Name.set_String()`, `PhonRulesOS.Add()`

#### `project.PhonologicalRule.Delete(rule_or_hvo)`
**Replaces:** `ILangProject.PhonologicalDataOA.PhonRulesOS.Remove()`

#### `project.PhonologicalRule.Find(name, wsHandle=None)`
**Replaces:** Phonological rule search by name

#### `project.PhonologicalRule.Exists(name, wsHandle=None)`
**Replaces:** Rule existence check via search

#### `project.PhonologicalRule.GetName(rule_or_hvo, wsHandle=None)`
**Replaces:** `IPhPhonRule.Name.get_String()`, `ITsString.Text`

#### `project.PhonologicalRule.SetName(rule_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IPhPhonRule.Name.set_String()`

#### `project.PhonologicalRule.GetDescription(rule_or_hvo, wsHandle=None)`
**Replaces:** `IPhPhonRule.Description.get_String()`, `ITsString.Text`

#### `project.PhonologicalRule.SetDescription(rule_or_hvo, description, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IPhPhonRule.Description.set_String()`

#### `project.PhonologicalRule.GetStratum(rule_or_hvo)`
**Replaces:** `IPhPhonRule.StratumRA` property access (returns `IMoStratum`)

#### `project.PhonologicalRule.SetStratum(rule_or_hvo, stratum)`
**Replaces:** `IPhPhonRule.StratumRA` property assignment

#### `project.PhonologicalRule.GetDirection(rule_or_hvo)`
**Replaces:** `IPhPhonRule.Direction` property access (0=left-to-right, 1=right-to-left, 2=simultaneous)

#### `project.PhonologicalRule.SetDirection(rule_or_hvo, direction)`
**Replaces:** `IPhPhonRule.Direction` property assignment

#### `project.PhonologicalRule.SetLeftContext(rule_or_hvo, context)`
**Replaces:** `IPhPhonRule.StrucDescOS[0].LeftContextOA` assignment

#### `project.PhonologicalRule.SetRightContext(rule_or_hvo, context)`
**Replaces:** `IPhPhonRule.StrucDescOS[0].RightContextOA` assignment

---

## Phase 14: Data Notebook Operations

### DataNotebookOperations

Methods for research notebook record management:

#### `project.DataNotebook.GetAll()`
**Replaces:** `IRnResearchNbkRepository.AllInstances()` iteration (top-level records only)

#### `project.DataNotebook.Create(title, content=None, wsHandle=None)`
**Replaces:** `IRnGenericRecFactory.Create()`, `IRnGenericRec.Title.set_String()`, `IRnGenericRec.Text.set_String()`, `IRnResearchNbkRepository.RecordsOC.Add()`

#### `project.DataNotebook.Delete(record_or_hvo)`
**Replaces:** `IRnResearchNbkRepository.RecordsOC.Remove()` or `SubRecordsOS.Remove()`

#### `project.DataNotebook.Find(title, wsHandle=None)`
**Replaces:** Notebook record search by title

#### `project.DataNotebook.Exists(title, wsHandle=None)`
**Replaces:** Record existence check via search

#### `project.DataNotebook.GetTitle(record_or_hvo, wsHandle=None)`
**Replaces:** `IRnGenericRec.Title.get_String()`, `ITsString.Text`

#### `project.DataNotebook.SetTitle(record_or_hvo, title, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IRnGenericRec.Title.set_String()`

#### `project.DataNotebook.GetContent(record_or_hvo, wsHandle=None)`
**Replaces:** `IRnGenericRec.Text.get_String()`, `ITsString.Text`

#### `project.DataNotebook.SetContent(record_or_hvo, content, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IRnGenericRec.Text.set_String()`

#### `project.DataNotebook.GetRecordType(record_or_hvo)`
**Replaces:** `IRnGenericRec.Type` property access (returns `ICmPossibility`)

#### `project.DataNotebook.SetRecordType(record_or_hvo, record_type)`
**Replaces:** `IRnGenericRec.Type` property assignment

#### `project.DataNotebook.GetAllRecordTypes()`
**Replaces:** `ILangProject.RecTypesOA.PossibilitiesOS` list conversion

#### `project.DataNotebook.FindRecordTypeByName(type_name, wsHandle=None)`
**Replaces:** Record type search by name in types list

#### `project.DataNotebook.GetDateCreated(record_or_hvo)`
**Replaces:** `IRnGenericRec.DateCreated` property access

#### `project.DataNotebook.GetDateModified(record_or_hvo)`
**Replaces:** `IRnGenericRec.DateModified` property access

#### `project.DataNotebook.GetDateOfEvent(record_or_hvo)`
**Replaces:** `IRnGenericRec.DateOfEvent` property access

#### `project.DataNotebook.SetDateOfEvent(record_or_hvo, date)`
**Replaces:** `IRnGenericRec.DateOfEvent` property assignment (accepts `DateTime` or string)

#### `project.DataNotebook.GetSubRecords(record_or_hvo)`
**Replaces:** `IRnGenericRec.SubRecordsOS` list conversion

#### `project.DataNotebook.CreateSubRecord(parent_record_or_hvo, title, content=None, wsHandle=None)`
**Replaces:** `IRnGenericRecFactory.Create()`, `IRnGenericRec.SubRecordsOS.Add()`

#### `project.DataNotebook.GetParentRecord(record_or_hvo)`
**Replaces:** `IRnGenericRec.Owner` property access with `IRnGenericRec` type check

#### `project.DataNotebook.GetResearchers(record_or_hvo)`
**Replaces:** `IRnGenericRec.Researchers` list conversion (returns `ICmPerson` objects)

#### `project.DataNotebook.AddResearcher(record_or_hvo, person)`
**Replaces:** `IRnGenericRec.Researchers.Add()`

#### `project.DataNotebook.RemoveResearcher(record_or_hvo, person)`
**Replaces:** `IRnGenericRec.Researchers.Remove()`

#### `project.DataNotebook.GetParticipants(record_or_hvo)`
**Replaces:** `IRnGenericRec.Participants` list conversion (returns `ICmPerson` objects)

#### `project.DataNotebook.AddParticipant(record_or_hvo, person)`
**Replaces:** `IRnGenericRec.Participants.Add()`

#### `project.DataNotebook.RemoveParticipant(record_or_hvo, person)`
**Replaces:** `IRnGenericRec.Participants.Remove()`

#### `project.DataNotebook.GetTexts(record_or_hvo)`
**Replaces:** `IRnGenericRec.TextsRC` list conversion (returns `IText` objects)

#### `project.DataNotebook.LinkToText(record_or_hvo, text)`
**Replaces:** `IRnGenericRec.TextsRC.Add()`

#### `project.DataNotebook.UnlinkFromText(record_or_hvo, text)`
**Replaces:** `IRnGenericRec.TextsRC.Remove()`

#### `project.DataNotebook.GetMediaFiles(record_or_hvo)`
**Replaces:** `IRnGenericRec.MediaFilesOS` list conversion (returns `ICmFile` objects)

#### `project.DataNotebook.AddMediaFile(record_or_hvo, media_file)`
**Replaces:** `IRnGenericRec.MediaFilesOS.Add()`

#### `project.DataNotebook.RemoveMediaFile(record_or_hvo, media_file)`
**Replaces:** `IRnGenericRec.MediaFilesOS.Remove()`

#### `project.DataNotebook.GetStatus(record_or_hvo)`
**Replaces:** `IRnGenericRec.Status` property access (returns `ICmPossibility`)

#### `project.DataNotebook.SetStatus(record_or_hvo, status)`
**Replaces:** `IRnGenericRec.Status` property assignment (accepts `ICmPossibility` or status name string)

#### `project.DataNotebook.GetAllStatuses()`
**Replaces:** `ILangProject.StatusOA.PossibilitiesOS` list conversion

#### `project.DataNotebook.FindStatusByName(status_name, wsHandle=None)`
**Replaces:** Status search by name in status list

#### `project.DataNotebook.FindByDate(start_date=None, end_date=None)`
**Replaces:** Filtered iteration of records by `DateOfEvent` range

#### `project.DataNotebook.FindByResearcher(person)`
**Replaces:** Filtered iteration of records by `Researchers` collection membership

#### `project.DataNotebook.FindByType(record_type)`
**Replaces:** Filtered iteration of records by `Type` property matching

#### `project.DataNotebook.GetGuid(record_or_hvo)`
**Replaces:** `IRnGenericRec.Guid` property access

#### `project.DataNotebook.GetConfidence(record_or_hvo)`
**Replaces:** `IRnGenericRec.Confidence` property access (returns `ICmPossibility`)

#### `project.DataNotebook.SetConfidence(record_or_hvo, confidence)`
**Replaces:** `IRnGenericRec.Confidence` property assignment

---

## Recent Additions (Post-v2.0)

> Public-method surface added after the v2.0.0 baseline (the 14 phases above). Grouped by Operations class rather than phase number, because the post-v2.0 work cuts across multiple phase boundaries: Phase 5 (a–e) expanded the morphology / phonology surface, Phase 6 (a–d) added catalog importers in four different domains, and assorted Q-series follow-ups added FLExProject-level helpers and the MSA wrapper. Each entry documents the LCM call(s) it wraps; methods marked **(supersedes Phase 13)** were stubs in Phase 13 that are now backed by real implementations.

### FLExProject (top-level)

#### `project.GetFactory(interface_type)`
**Replaces:** `ILcmServiceLocator.GetInstance<T>()` generic-method invocation. Tries the overload-resolved `ServiceLocator.GetInstance(Type)` path first, then falls back to reflection over the parameterless generic `GetInstance<T>()` with `clr.GetClrType(interface_type)`. Caches the resolved `MethodInfo` on the FLExProject instance.

#### `project.GetService(interface_type)`
**Replaces:** `ILcmServiceLocator.GetService(Type)` — thin discoverable wrapper.

#### `project.ImportLocalizedLists(language_code, progress=None)`
**Replaces:** `SIL.LCModel.Application.ApplicationServices.XmlTranslatedLists.ImportTranslatedListsForWs()`, with path resolution into `<FWCodeDir>/Templates/LocalizedLists-<lang>.zip` and FLEx-specific error wrapping.

#### `project.ImportLocalizedListsForEnabledWS(progress=None)`
**Replaces:** Iteration over `ILangProject.CurAnalysisWss` calling `XmlTranslatedLists.ImportTranslatedListsForWs()` for each WS whose `LocalizedLists-XX.zip` exists, with per-WS error isolation.

### MSAOperations (`project.MSA`)

Brand new in Phase 5/6+. Wraps the four concrete MoMsa subtypes (kStem / kDeriv / kInfl / kUnclassified) behind a common SandboxGenericMSA + attach-to-sense idiom, so callers don't have to wire ServiceLocator + factory + SandboxGenericMSA themselves.

#### `project.MSA.CreateStem(sense, pos)`
**Replaces:** `ILcmServiceLocator.GetService(IMoStemMsaFactory)`, `SandboxGenericMSA{ MsaType = kStem, MainPOS = pos }`, `IMoStemMsaFactory.Create(sense.Owner, sandbox)`, `ILexSense.MorphoSyntaxAnalysisRA` assignment.

#### `project.MSA.CreateDerivAff(sense, from_pos, to_pos)`
**Replaces:** Same idiom with `IMoDerivAffMsaFactory`, `MsaType = kDeriv`, `MainPOS = from_pos`, `SecondaryPOS = to_pos`.

#### `project.MSA.CreateInflAff(sense, pos, slots=None)`
**Replaces:** Same idiom with `IMoInflAffMsaFactory`, `MsaType = kInfl`, plus `IMoInflAffMsa.SlotsRC.Add()` for each slot in the optional collection.

#### `project.MSA.CreateUnclassifiedAffix(sense, pos)`
**Replaces:** Same idiom with `IMoUnclassifiedAffixMsaFactory`, `MsaType = kUnclassified`.

#### `project.MSA.SetStemMsaPos(sense, pos)`
**Replaces:** `IMoStemMsa(ILexSense.MorphoSyntaxAnalysisRA).PartOfSpeechRA` assignment, after a type guard that rejects non-stem existing MSAs.

### PhonologicalRuleOperations (`project.PhonRules`)

The Phase 13 entries (GetAll, Create, Delete, Find, Exists, GetName/SetName, GetDescription/SetDescription, GetStratum/SetStratum, GetDirection/SetDirection, SetLeftContext, SetRightContext) remain accurate. The Phase 5e additions below provide alpha-feature constraints and a high-level rule composer (`WireRule`), which is the preferred entry point for wiring rule inputs, outputs, and contexts.

#### `project.PhonRules.MakeConstraint(feature_or_hvo)`
**Replaces:** `ILcmServiceLocator.GetService(IPhFeatureConstraintFactory).Create()`, `ILangProject.PhonologicalDataOA.FeatConstraintsOS.Add()`, `IPhFeatureConstraint.FeatureRA` assignment (ownership-before-property ordering).

#### `project.PhonRules.DeleteConstraint(constraint_or_hvo)`
**Replaces:** `ILangProject.PhonologicalDataOA.FeatConstraintsOS.Remove()` with explicit presence check.

#### `project.PhonRules.GetConstraints()`
**Replaces:** `ILangProject.PhonologicalDataOA.FeatConstraintsOS` list conversion.

#### `project.PhonRules.WireRule(rule_or_hvo, input_pattern=None, output_change=None, left_context=None, right_context=None, mode="replace")`
**Replaces:** Composite operation across `IPhSegmentRule.StrucDescOS`, `IPhSegRuleRHS.StrucChangeOS`, `IPhContextOrVar.LeftContextOA / RightContextOA`, the IPhSequenceContext / IPhSimpleContextSeg / IPhSimpleContextNC / IPhSimpleContextBdry factories, plus `PlusConstrRS / MinusConstrRS` wiring for alpha-feature constraints. High-level SPE-notation composer that hides the multi-stage context construction.

#### `project.PhonRules.Duplicate(item_or_hvo, insert_after=True, deep=True)`
**Replaces:** Type-aware deep clone for `IPhRegularRule` / `IPhMetathesisRule` / `IPhReduplicationRule` via `lcm_casting.clone_properties()`, with optional insertion adjacent to the source in `PhonRulesOS`.

#### `project.PhonRules.GetSyncableProperties(item)`
**Replaces:** Per-property reflection of an IPhSegmentRule into a dict suitable for the sync engine's comparison stage.

#### `project.PhonRules.CompareTo(item1, item2, ops1=None, ops2=None)`
**Replaces:** Cross-project diff of two phonological rules; pairs with `GetSyncableProperties` for the sync workflow.

### NaturalClassOperations (`project.NaturalClasses`)

Phase 5d added the feature-based subtype and unified read/write across the two concrete shapes (IPhNCSegments vs IPhNCFeatures).

#### `project.NaturalClasses.Find(name, wsHandle=None)`
**Replaces:** NFD-normalized search through `ILangProject.PhonologicalDataOA.NaturalClassesOS` by `IPhNaturalClass.Name.get_String()`.

#### `project.NaturalClasses.Exists(name, wsHandle=None)`
**Replaces:** Existence check via `Find()`.

#### `project.NaturalClasses.CreateFeatureBased(name, abbreviation=None, specs=None)`
**Replaces:** `ILcmServiceLocator.GetService(IPhNCFeaturesFactory).Create()`, `NaturalClassesOS.Add()`, name/abbreviation strings, and `IPhNCFeatures.FeaturesOA` population via `PhonFeatureOperations.MakeFeatStruc()` when `specs` is supplied.

#### `project.NaturalClasses.GetType(nc_or_hvo)`
**Replaces:** Concrete-type detection via `hasattr(nc, "FeaturesOA")` / `hasattr(nc, "SegmentsRC")` — returns `"features"` / `"segments"` / `ClassName` fallback. No direct LCM equivalent.

#### `project.NaturalClasses.GetFeatures(nc_or_hvo)`
**Replaces:** `IPhNCFeatures.FeaturesOA` property access; returns the owned IFsFeatStruc or None.

#### `project.NaturalClasses.SetFeatures(nc_or_hvo, specs)`
**Replaces:** Replacement of `IPhNCFeatures.FeaturesOA` via the IFsFeatStrucFactory + IFsClosedValueFactory chain (ownership-first attachment, then per-spec value assignment).

#### `project.NaturalClasses.Duplicate(item_or_hvo, insert_after=True)`
**Replaces:** Type-aware clone dispatching on `IPhNCSegments` (copy SegmentsRC) vs `IPhNCFeatures` (copy FeaturesOA via clone_properties).

#### `project.NaturalClasses.GetSyncableProperties(item)` / `CompareTo(item1, item2, ops1=None, ops2=None)`
**Replaces:** Sync-engine integration; per-property reflection and pairwise diff over the two NC subtypes.

### PhonemeOperations (`project.Phonemes`)

Phase 5d/6d added catalog-driven code management and IPA symbol handling.

#### `project.Phonemes.FindCode(phoneme_or_hvo, representation, wsHandle=None)`
**Replaces:** Iteration over `IPhPhoneme.CodesOS` with NFD-normalized comparison on `IPhCode.Representation.get_String()`.

#### `project.Phonemes.ReplaceCode(phoneme_or_hvo, old_code_or_repr, new_representation, wsHandle=None)`
**Replaces:** `RemoveCode()` + `AddCode()` round-trip on `IPhPhoneme.CodesOS`. Returns the new IPhCode.

#### `project.Phonemes.GetBasicIPASymbol(phoneme_or_hvo, wsHandle=None)`
**Replaces:** `IPhPhoneme.BasicIPASymbol.get_String()` (or scalar `BasicIPASymbol` per-build fallback), `ITsString.Text`. Handles both IMultiString and ITsString shapes the property takes across FLEx builds.

#### `project.Phonemes.SetBasicIPASymbol(phoneme_or_hvo, ipa, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IPhPhoneme.BasicIPASymbol.set_String()` (with scalar-property fallback for older builds).

#### `project.Phonemes.Duplicate(item_or_hvo, insert_after=True, deep=True)`
**Replaces:** `IPhPhonemeFactory.Create()`, `PhonemesOC.Add()`, deep-clone of `Representation` / `Description` multistrings and `FeaturesOA` IFsFeatStruc via `lcm_casting.clone_properties()`, optional CodesOS clone.

#### `project.Phonemes.ImportCatalog(progress=None, force=False)`
**Replaces:** XML parse of `<FWCodeDir>/Templates/BasicIPAInfo.xml` (via `Shared.catalog.parse_basic_ipa_info`), creation of IPhPhonemes through IPhPhonemeFactory, attachment to `IPhPhonemeSet.PhonemesOC`, cross-reference of BasicIPAInfo feature ids to existing IFsClosedFeature/IFsSymFeatVal objects loaded from PhonFeats. Non-empty-set guard requires `force=True` to re-import (no canonical GUIDs to dedupe against).

#### `project.Phonemes.GetSyncableProperties(item)` / `ApplySyncableProperties(item, props, ws_map=None, fill_gaps=False)` / `CompareTo(item1, item2, ops1=None, ops2=None)`
**Replaces:** Sync-engine integration. `GetSyncableProperties` returns guarded `{ws_id: text}` dicts for `Name` / `Description` / `BasicIPASymbol` (tolerating BasicIPASymbol's per-build IMultiString-vs-scalar shape — fixes the `ITsString.get_String` crash), plus `FeaturesGuid` and a `Features` list of `{FeatureGuid, ValueGuid}` specs from `FeaturesOA.FeatureSpecsOC`. `ApplySyncableProperties` re-applies the multistrings, sets BasicIPASymbol through the shape-tolerant setter, and rewires the `Features` specs against the target project's feature system by GUID (issue #222).

### PhonFeatureOperations (`project.PhonFeatures`)

New module in Phase 5b. Manages `ILangProject.PhFeatureSystemOA` (IFsFeatureSystem) — the phonological-feature half of the FLEx feature system. Mirrors InflectionFeatureOperations and inherits `CatalogBackedMixin`.

#### `project.PhonFeatures.GetAll()`
**Replaces:** `ILangProject.PhFeatureSystemOA.FeaturesOC` list conversion.

#### `project.PhonFeatures.GetName(feature_or_hvo, wsHandle=None)`
**Replaces:** `IFsFeatDefn.Name.get_String()`, `ITsString.Text`.

#### `project.PhonFeatures.GetAbbreviation(feature_or_hvo, wsHandle=None)`
**Replaces:** `IFsFeatDefn.Abbreviation.get_String()`, `ITsString.Text`.

#### `project.PhonFeatures.GetDescription(feature_or_hvo, wsHandle=None)`
**Replaces:** `IFsFeatDefn.Description.get_String()`, `ITsString.Text`.

#### `project.PhonFeatures.GetValues(feature_or_hvo)`
**Replaces:** `IFsClosedFeature.ValuesOC` list conversion (returns IFsSymFeatVal objects).

#### `project.PhonFeatures.Find(name, wsHandle=None)`
**Replaces:** Iteration through `PhFeatureSystemOA.FeaturesOC` with NFD-normalized name match.

#### `project.PhonFeatures.Exists(name, wsHandle=None)`
**Replaces:** Existence check via `Find()`.

#### `project.PhonFeatures.Create(name, abbreviation, catalogSourceId=None)`
**Replaces:** `IFsClosedFeatureFactory.Create()`, `PhFeatureSystemOA.FeaturesOC.Add()`, `Name.set_String()`, `Abbreviation.set_String()`, optional `CatalogSourceId` assignment. When `catalogSourceId` starts with `PHON:`, defers to `CreateFromCatalog()` (from CatalogBackedMixin) for canonical-GUID + values.

#### `project.PhonFeatures.SetName(feature_or_hvo, name, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IFsFeatDefn.Name.set_String()` (also works on IFsSymFeatVal).

#### `project.PhonFeatures.SetAbbreviation(feature_or_hvo, abbrev, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IFsFeatDefn.Abbreviation.set_String()`.

#### `project.PhonFeatures.SetDescription(feature_or_hvo, description, wsHandle=None)`
**Replaces:** `TsStringUtils.MakeString()`, `IFsFeatDefn.Description.set_String()`.

#### `project.PhonFeatures.Delete(feature_or_hvo)`
**Replaces:** `PhFeatureSystemOA.FeaturesOC.Remove()` for closed features, or `IFsClosedFeature.ValuesOC.Remove()` for values nested under a feature.

#### `project.PhonFeatures.CreateValue(feature_or_hvo, name, abbreviation, value_marker=None)`
**Replaces:** `IFsSymFeatValFactory.Create()`, `IFsClosedFeature.ValuesOC.Add()` (ownership-first), `Name.set_String()`, `Abbreviation.set_String()`.

#### `project.PhonFeatures.DeleteValue(value_or_hvo)`
**Replaces:** `IFsClosedFeature.ValuesOC.Remove()` after walking up the owner chain to the parent feature.

#### `project.PhonFeatures.MakeFeatStruc(specs, owner=None)`
**Replaces:** `IFsFeatStrucFactory.Create()`, attachment to `owner.FeaturesOA` (Phase 2 ownership rule applied before populating specs), one `IFsClosedValueFactory.Create()` + `FeatureSpecsOC.Add()` per `(feature, value)` pair.

#### `project.PhonFeatures.ImportCatalog(progress=None)` (inherited from `CatalogBackedMixin`)
**Replaces:** XML parse of `<FWCodeDir>/Templates/PhonFeatsEticGlossList.xml` (via `parse_etic_gloss_list`), canonical-GUID dedupe against existing `FeaturesOC`, per-feature `IFsClosedFeatureFactory.Create()` and per-value `IFsSymFeatValFactory.Create()` with localized name/abbreviation/description across all enabled WSes.

#### `project.PhonFeatures.CreateFromCatalog(source_id, parent=None)` (inherited from `CatalogBackedMixin`)
**Replaces:** Catalog lookup by `PHON:`-prefixed id, idempotent create-or-return-existing of the corresponding IFsClosedFeature + its IFsSymFeatVal children.

#### `project.PhonFeatures.GetSyncableProperties(item)` / `ApplySyncableProperties(item, props, ws_map=None, fill_gaps=False)`
**Replaces:** Sync-engine integration (issue #222). `GetSyncableProperties` returns `{ws_id: text}` dicts for `Name` / `Abbreviation` / `Description`, the plain `CatalogSourceId` provenance tag, and a `Values` list — one entry per owned `IFsSymFeatVal`, each carrying its own `Guid` plus name/abbreviation/description — so a closed feature is not synced as an empty shell. `ApplySyncableProperties` applies the feature's own fields via the base loop, then co-creates the owned values GUID-aligned (`IFsSymFeatValFactory.Create(guid, feature)`, falling back to `Create(guid)` + `ValuesOC.Add()`), reusing any existing value with a matching GUID so re-application is idempotent.

### InflectionFeatureOperations (`project.InflectionFeatures`, alias `project.Features`)

Phase 5a/d expanded the surface to match PhonFeatureOperations for symmetry.

#### `project.InflectionFeatures.Find(name, wsHandle=None)`
**Replaces:** Iteration through `ILangProject.MsFeatureSystemOA.FeaturesOC` with NFD-normalized match against `IFsFeatDefn.Name`.

#### `project.InflectionFeatures.Exists(name, wsHandle=None)`
**Replaces:** Existence check via `Find()`.

#### `project.InflectionFeatures.Create(name, abbreviation, type="closed", catalogSourceId=None)`
**Replaces:** `IFsClosedFeatureFactory.Create()` or `IFsComplexFeatureFactory.Create()` depending on `type`, `MsFeatureSystemOA.FeaturesOC.Add()`, name/abbreviation strings. When `catalogSourceId` starts with `INFL:`, defers to `CreateFromCatalog()` (canonical GUID + values).

#### `project.InflectionFeatures.CreateValue(feature_or_hvo, name, abbreviation, value_marker=None)`
**Replaces:** `IFsSymFeatValFactory.Create()`, `IFsClosedFeature.ValuesOC.Add()` (ownership-first), name/abbreviation set.

#### `project.InflectionFeatures.CreateClosedFeatureWithValues(name, abbreviation, values, catalogSourceId=None)`
**Replaces:** Compound of `Create(type="closed")` + N×`CreateValue()`. Validates the `[(value_name, value_abbreviation), ...]` tuples up front. Returns `(feature, [values])`.

#### `project.InflectionFeatures.MakeFeatStruc(specs, owner=None)`
**Replaces:** `IFsFeatStrucFactory.Create()`, owner-attach, per-spec `IFsClosedValueFactory.Create()` + `FeatureSpecsOC.Add()` — mirrors the PhonFeatures version but produces an inflection feature structure suitable for MSAs and inflection templates.

#### `project.InflectionFeatures.TypeFind(name, wsHandle=None)`
**Replaces:** Iteration through `ILangProject.MsFeatureSystemOA.TypesOC` with name match.

#### `project.InflectionFeatures.TypeCreate(name, abbreviation)`
**Replaces:** `IFsFeatStrucTypeFactory.Create()`, `MsFeatureSystemOA.TypesOC.Add()`, name/abbreviation set. Provides the IFsFeatStrucType objects features can group under.

#### `project.InflectionFeatures.ImportCatalog(progress=None)` (inherited from `CatalogBackedMixin`)
**Replaces:** XML parse of `<FWCodeDir>/Templates/EticGlossList.xml` (via `parse_etic_gloss_list`), canonical-GUID dedupe, per-feature/per-value factory creation with localized strings.

#### `project.InflectionFeatures.CreateFromCatalog(source_id, parent=None)` (inherited)
**Replaces:** Single-item create-or-return from `INFL:`-prefixed catalog id.

### SemanticDomainOperations (`project.SemanticDomains`)

Phase 6b added native-XML catalog import.

#### `project.SemanticDomains.ImportCatalog(progress=None, force=False)`
**Replaces:** `SIL.LCModel.Application.ApplicationServices.XmlList.ImportList()` against `<FWCodeDir>/Templates/SemDom.xml` targeting `ILangProject.SemanticDomainListOA`. Adds an idempotency guard (refuses when the list is non-empty unless `force=True`) because XmlList.ImportList appends without GUID dedup. Returns the post-import top-level domain count.

### AnthropologyOperations (`project.Anthropology`)

Phase 6c added native-XML catalog import plus the OCM-Frame sibling.

#### `project.Anthropology.ImportCatalog(progress=None, force=False)`
**Replaces:** `XmlList.ImportList()` against `<FWCodeDir>/Templates/OCM.xml` targeting `ILangProject.AnthroListOA`. Same idempotency-guard contract as `SemanticDomains.ImportCatalog`.

#### `project.Anthropology.ImportFrameCatalog(progress=None, force=False)`
**Replaces:** Same `XmlList.ImportList()` plumbing pointed at `OCM-Frame.xml` (the framework variant that ships alongside OCM.xml). The usual workflow is `ImportCatalog()` then `ImportFrameCatalog(force=True)` to layer framework entries on top.

### Phase 13 PhonologicalRule entries — superseded notes

The Phase 13 entries for `Find()`, `Exists()`, `SetLeftContext()`, and `SetRightContext()` remain accurate but should be understood as low-level primitives that `WireRule()` composes. For most user code, `WireRule(rule, input_pattern=..., output_change=..., left_context=..., right_context=...)` is the preferred entry point.

---

## Common LibLCM Patterns

### Factory Pattern
- **flexlibs:** `project.ClassName.Create(...)`
- **LibLCM:** `ServiceLocator.GetInstance(IClassNameFactory).Create()`

### Repository Pattern
- **flexlibs:** `project.ClassName.GetAll()`
- **LibLCM:** `ServiceLocator.GetInstance(IClassNameRepository).AllInstances()` or `ObjectsIn(IClassNameRepository)`

### String Handling
- **flexlibs:** Methods handle string conversion automatically
- **LibLCM:** `TsStringUtils.MakeString(text, wsHandle)`, `ITsString.Text`

### Collection Access
- **flexlibs:** List/generator methods with Python iteration
- **LibLCM:** Direct `.NET` collection access (`OS`, `OC`, `RC`, `RS`, `OA`, `RA` suffixes)

### Property Access
- **flexlibs:** `Get*/Set*` methods with validation and error handling
- **LibLCM:** Direct property access/assignment

---

## Notes

1. **HVO Support:** Most flexlibs methods accept either objects or HVOs (database IDs)
2. **Writing Systems:** Many methods have optional `wsHandle` parameters that default to appropriate WS
3. **Error Handling:** Flexlibs wraps LibLCM exceptions with custom exception types
4. **Validation:** Input validation and null checking is handled automatically
5. **Reflection Usage:** Some properties like `SenseNumber` require reflection in LibLCM but are exposed as regular methods in flexlibs

---

## Summary Statistics

**Total Phases Documented:** 14 of 14 (Complete) + Post-v2.0 additions
**Total Operations Classes:** 35+
**Total Methods Documented:** 400+

### Coverage by Phase:
- **Phase 1:** Core Text & Lexicon Objects (3 classes, 40+ methods) ✓
- **Phase 2:** Lexical Entry Operations (1 class, 22 methods) ✓
- **Phase 3:** Reversal Index Operations (1 class, 18 methods) ✓
- **Phase 4:** Writing System Operations (1 class, 18 methods) ✓
- **Phase 5:** Morphology Type & Rule Operations (1 class, methods noted) ✓
- **Phase 6:** Example Sentences & Pictures (2 classes, 20+ methods) ✓
- **Phase 7:** Lexical Sense Operations (1 class, 30+ methods) ✓
- **Phase 8:** Pronunciations, Variants & Allomorphs (3 classes, 25+ methods) ✓
- **Phase 9:** WfiAnalysis, Filters & Discourse (3 classes, 15+ methods) ✓
- **Phase 10:** Variant Forms & Discourse (1 class, 7+ methods) ✓
- **Phase 11:** Allomorphs, Media, Persons & Agents (4 classes, 35+ methods) ✓
- **Phase 12:** Translation Types, Semantic Domains & Possibility Lists (3 classes, 20+ methods) ✓
- **Phase 13:** Checks, Overlays, Settings & Phonological Rules (4 classes, 60+ methods) ✓
- **Phase 14:** Data Notebook Operations (1 class, 42 methods) ✓
- **Post-v2.0 (Phase 5/6+):** Alpha-feature constraints + WireRule composer, feature-based natural classes, IPA management, PhonFeatures module, expanded InflectionFeatures, MSAOperations, catalog imports (SemDom / OCM / OCM-Frame / BasicIPAInfo / PhonFeats / EticGloss / GOLD), LocalizedLists, FLExProject GetFactory/GetService (9 classes touched, 50+ methods) ✓

---

**Document Version:** 2.1 (Phase 5/6 refresh)
**Original Baseline:** 2025-11-23 (v2.0, 14 phases)
**Last Refreshed:** 2026-05-27
**Status:** All 14 phases plus post-v2.0 additions documented with LibLCM API mappings
