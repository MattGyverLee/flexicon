# Scripture Operations Test Specifications

## Overview

This document provides detailed test specifications for all 6 Scripture Operations classes in flexicon. These classes handle Scripture books, sections, headings, references, and import workflows.

**Test Scope**: 6 Scripture Operations classes
**Related Classes**: ParagraphOperations, TextOperations, StTextOperations

---

## Table of Contents

1. [ScrBookOperations Tests](#scrbookoperations-tests)
2. [ScrSectionOperations Tests](#scrsectionoperations-tests)
3. [ScrSectionHeadOperations Tests](#scrsectionheadoperations-tests)
4. [ScrBookRefOperations Tests](#scrbookrefoperations-tests)
5. [ScrImportSetOperations Tests](#scrimportsetoperations-tests)
6. [ScrMarkerMappingOperations Tests](#scrmarkermappingoperations-tests)

---

## ScrBookOperations Tests

### Class Information
- **LCM Interface**: IScrBook
- **Parent**: Scripture (IScripture.ScriptureBooksOS)
- **Children**: Sections (IScrBook.SectionsOS), Title (IScrBook.TitleOA)
- **Key Properties**: CanonicalNum, Name (MultiString), BookId (string), FootnotesOS

### Test_Create_MinimalBook

**Setup**:
```python
project = FLExProject()
project.OpenProject("TestProject", writeEnabled=True)
```

**Action**:
```python
book = project.ScrBooks.Create(1)  # Genesis
```

**Verify**:
- `book is not None`
- `book.CanonicalNum == 1`
- `book in project.Scripture.ScriptureBooksOS`
- `book.SectionsOS.Count == 0` (no sections yet)
- `book.TitleOA is not None` (title object exists)
- `book.Guid != System.Guid.Empty`

**Cleanup**:
```python
project.ScrBooks.Delete(book)
project.CloseProject()
```

### Test_Create_BookWithName

**Action**:
```python
book = project.ScrBooks.Create(1, name="Genesis", wsHandle="en")
```

**Verify**:
- `project.ScrBooks.GetName(book, "en") == "Genesis"`
- Name set in analysis writing system (English)

### Test_Create_BookWithAbbreviation

**Action**:
```python
book = project.ScrBooks.Create(1, abbreviation="Gen", wsHandle="en")
```

**Verify**:
- `project.ScrBooks.GetAbbreviation(book, "en") == "Gen"`

### Test_Create_DuplicateCanonicalNumber

**Action**:
```python
book1 = project.ScrBooks.Create(1)  # Genesis
book2 = project.ScrBooks.Create(1)  # Try to create another Genesis
```

**Verify**:
- Either: Second creation fails with FP_ParameterError
- Or: Second creation succeeds but creates second instance (homograph-like behavior)
- Document actual behavior for future reference

### Test_Create_InvalidCanonicalNumber

**Action**:
```python
book = project.ScrBooks.Create(0)  # Invalid book number
```

**Verify**:
- Raises FP_ParameterError
- Error message indicates valid range (1-66 or extended)

### Test_Create_ReadOnlyProject

**Setup**:
```python
project.OpenProject("TestProject", writeEnabled=False)
```

**Action**:
```python
book = project.ScrBooks.Create(1)
```

**Verify**:
- Raises FP_ReadOnlyError

### Test_Find_ExistingBook

**Setup**:
```python
created_book = project.ScrBooks.Create(1)
```

**Action**:
```python
found_book = project.ScrBooks.Find(1)  # Find by canonical number
```

**Verify**:
- `found_book is not None`
- `found_book.Hvo == created_book.Hvo`
- `found_book.CanonicalNum == 1`

### Test_Find_NonExistentBook

**Action**:
```python
found_book = project.ScrBooks.Find(99)  # Book doesn't exist
```

**Verify**:
- `found_book is None` (returns None, not exception)

### Test_Find_NullCanonicalNumber

**Action**:
```python
found_book = project.ScrBooks.Find(None)
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetAll_Empty

**Setup**:
```python
# Clean project with no scripture books
for book in project.ScrBooks.GetAll():
    project.ScrBooks.Delete(book)
```

**Action**:
```python
books = list(project.ScrBooks.GetAll())
```

**Verify**:
- `len(books) == 0`
- Returns empty iterator (not None)

### Test_GetAll_Multiple

**Setup**:
```python
project.ScrBooks.Create(1)  # Genesis
project.ScrBooks.Create(2)  # Exodus
project.ScrBooks.Create(40)  # Matthew
```

**Action**:
```python
books = list(project.ScrBooks.GetAll())
```

**Verify**:
- `len(books) == 3`
- All three books present in collection

### Test_Delete_ExistingBook

**Setup**:
```python
book = project.ScrBooks.Create(1)
book_guid = book.Guid
```

**Action**:
```python
project.ScrBooks.Delete(book)
```

**Verify**:
- Book no longer in Scripture.ScriptureBooksOS
- `project.ScrBooks.Find(1) is None`
- Object with book_guid no longer accessible

### Test_Delete_CascadeSections

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Test Section")
section_guid = section.Guid
```

**Action**:
```python
project.ScrBooks.Delete(book)
```

**Verify**:
- Section also deleted (cascade)
- Section object with section_guid no longer accessible

### Test_Delete_NullParameter

**Action**:
```python
project.ScrBooks.Delete(None)
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetCanonicalNum

**Setup**:
```python
book = project.ScrBooks.Create(1)
```

**Action**:
```python
num = project.ScrBooks.GetCanonicalNum(book)
```

**Verify**:
- `num == 1`

### Test_SetCanonicalNum

**Setup**:
```python
book = project.ScrBooks.Create(1)
```

**Action**:
```python
project.ScrBooks.SetCanonicalNum(book, 2)  # Change from Genesis to Exodus
```

**Verify**:
- `project.ScrBooks.GetCanonicalNum(book) == 2`
- Book still accessible
- May have implications for ordering

### Test_GetName_MultipleWritingSystems

**Setup**:
```python
book = project.ScrBooks.Create(1)
project.ScrBooks.SetName(book, "Genesis", wsHandle="en")
project.ScrBooks.SetName(book, "Génesis", wsHandle="es")
```

**Action**:
```python
name_en = project.ScrBooks.GetName(book, wsHandle="en")
name_es = project.ScrBooks.GetName(book, wsHandle="es")
```

**Verify**:
- `name_en == "Genesis"`
- `name_es == "Génesis"`
- MultiString supports multiple WS

### Test_GetAbbreviation

**Setup**:
```python
book = project.ScrBooks.Create(1)
project.ScrBooks.SetAbbreviation(book, "Gen", wsHandle="en")
```

**Action**:
```python
abbr = project.ScrBooks.GetAbbreviation(book, wsHandle="en")
```

**Verify**:
- `abbr == "Gen"`

### Test_GetBookId

**Setup**:
```python
book = project.ScrBooks.Create(1)
```

**Action**:
```python
book_id = project.ScrBooks.GetBookId(book)
```

**Verify**:
- `book_id` is a string (likely "GEN" or similar USFM code)
- Matches standard for canonical number 1

### Test_Integration_AddSectionToBook

**Setup**:
```python
book = project.ScrBooks.Create(1)
```

**Action**:
```python
section = project.ScrSections.Create(book, "Creation Account")
```

**Verify**:
- `section.Owner == book`
- `section in book.SectionsOS`
- `book.SectionsOS.Count == 1`

---

## ScrSectionOperations Tests

### Class Information
- **LCM Interface**: IScrSection
- **Parent**: ScrBook (IScrBook.SectionsOS)
- **Children**: HeadingOA (IScrTxtPara), ContentOA (StText with ParagraphsOS)
- **Key Properties**: VerseRefStart, VerseRefEnd, VerseRefMin, VerseRefMax

### Test_Create_MinimalSection

**Setup**:
```python
book = project.ScrBooks.Create(1)
```

**Action**:
```python
section = project.ScrSections.Create(book, heading="Introduction")
```

**Verify**:
- `section is not None`
- `section.Owner == book`
- `section in book.SectionsOS`
- `section.HeadOA is not None` (heading text object exists)
- `section.ContentOA is not None` (content text object exists)
- `project.ScrSections.GetHeading(section) == "Introduction"`

### Test_Create_SectionWithContent

**Setup**:
```python
book = project.ScrBooks.Create(1)
```

**Action**:
```python
section = project.ScrSections.Create(
    book,
    heading="Creation Account",
    content="In the beginning, God created..."
)
```

**Verify**:
- Heading is set
- Content paragraph created in ContentOA
- Content text retrievable

### Test_Create_NullBook

**Action**:
```python
section = project.ScrSections.Create(None, "Test")
```

**Verify**:
- Raises FP_NullParameterError

### Test_Create_EmptyHeading

**Setup**:
```python
book = project.ScrBooks.Create(1)
```

**Action**:
```python
section = project.ScrSections.Create(book, heading="")
```

**Verify**:
- Either: Allows empty heading (valid use case)
- Or: Raises FP_ParameterError if heading required
- Document actual behavior

### Test_GetHeading

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Creation Account")
```

**Action**:
```python
heading = project.ScrSections.GetHeading(section)
```

**Verify**:
- `heading == "Creation Account"`

### Test_SetHeading

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Old Heading")
```

**Action**:
```python
project.ScrSections.SetHeading(section, "New Heading")
```

**Verify**:
- `project.ScrSections.GetHeading(section) == "New Heading"`

### Test_GetContent

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Heading", "Content text here")
```

**Action**:
```python
content = project.ScrSections.GetContent(section)
```

**Verify**:
- `content` contains "Content text here"
- Content from first paragraph in ContentOA

### Test_AddParagraph

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Heading")
```

**Action**:
```python
para = project.ScrSections.AddParagraph(section, "Verse 1 text")
```

**Verify**:
- `para is not None`
- `para.Owner == section.ContentOA`
- `para in section.ContentOA.ParagraphsOS`
- Paragraph text set correctly

### Test_GetParagraphs

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Heading")
project.ScrSections.AddParagraph(section, "Para 1")
project.ScrSections.AddParagraph(section, "Para 2")
```

**Action**:
```python
paras = project.ScrSections.GetParagraphs(section)
```

**Verify**:
- `len(paras) == 2`
- Paragraphs in correct order

### Test_Delete_ExistingSection

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Test")
section_guid = section.Guid
```

**Action**:
```python
project.ScrSections.Delete(section)
```

**Verify**:
- Section removed from book.SectionsOS
- Section object no longer accessible by GUID

### Test_Delete_CascadeParagraphs

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Test")
para = project.ScrSections.AddParagraph(section, "Test para")
para_guid = para.Guid
```

**Action**:
```python
project.ScrSections.Delete(section)
```

**Verify**:
- Paragraph also deleted (cascade)
- Paragraph no longer accessible by GUID

### Test_VerseRefStart_Get

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Genesis 1")
```

**Action**:
```python
# Set verse reference to Genesis 1:1
project.ScrSections.SetVerseRefStart(section, bcv_ref)
verse_ref = project.ScrSections.GetVerseRefStart(section)
```

**Verify**:
- Verse reference retrieved correctly
- Matches set value

### Test_Integration_BookSectionParagraphHierarchy

**Setup**:
```python
# Create full hierarchy
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Creation")
para = project.ScrSections.AddParagraph(section, "In the beginning...")
```

**Verify**:
- `section.Owner == book`
- `para.Owner == section.ContentOA`
- `section in book.SectionsOS`
- `para in section.ContentOA.ParagraphsOS`
- Full hierarchy intact

---

## ScrSectionHeadOperations Tests

### Class Information
- **LCM Interface**: IScrTxtPara (specialized for section headings)
- **Parent**: ScrSection (IScrSection.HeadingOA)
- **Key Properties**: Contents (StText), StyleRules (for heading formatting)

### Test_Create_SectionHead

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, heading=None)  # No heading yet
```

**Action**:
```python
head = project.ScrSectionHeads.Create(section, "Major Section")
```

**Verify**:
- `head is not None`
- `section.HeadingOA == head`
- Heading text is "Major Section"

### Test_GetText

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Test Heading")
head = section.HeadingOA
```

**Action**:
```python
text = project.ScrSectionHeads.GetText(head)
```

**Verify**:
- `text == "Test Heading"`

### Test_SetText

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "Old Heading")
head = section.HeadingOA
```

**Action**:
```python
project.ScrSectionHeads.SetText(head, "New Heading")
```

**Verify**:
- `project.ScrSectionHeads.GetText(head) == "New Heading"`

### Test_MultipleWritingSystems

**Setup**:
```python
book = project.ScrBooks.Create(1)
section = project.ScrSections.Create(book, "English Heading")
head = section.HeadingOA
```

**Action**:
```python
project.ScrSectionHeads.SetText(head, "Spanish Heading", wsHandle="es")
heading_en = project.ScrSectionHeads.GetText(head, wsHandle="en")
heading_es = project.ScrSectionHeads.GetText(head, wsHandle="es")
```

**Verify**:
- `heading_en == "English Heading"`
- `heading_es == "Spanish Heading"`

---

## ScrBookRefOperations Tests

### Class Information
- **LCM Interface**: IScrBookRef (reference to canonical scripture books)
- **Purpose**: Used in mappings and references to track which book is being processed
- **Key Properties**: BookHvo (reference to IScrBook), Name

### Test_Create_BookRef

**Setup**:
```python
book = project.ScrBooks.Create(1)  # Genesis
```

**Action**:
```python
book_ref = project.ScrBookRefs.Create(book)
```

**Verify**:
- `book_ref is not None`
- `book_ref.BookHvo == book.Hvo`
- Reference points to correct book

### Test_GetBook

**Setup**:
```python
book = project.ScrBooks.Create(1)
book_ref = project.ScrBookRefs.Create(book)
```

**Action**:
```python
retrieved_book = project.ScrBookRefs.GetBook(book_ref)
```

**Verify**:
- `retrieved_book.Hvo == book.Hvo`
- `retrieved_book.CanonicalNum == 1`

### Test_Create_NullBook

**Action**:
```python
book_ref = project.ScrBookRefs.Create(None)
```

**Verify**:
- Raises FP_NullParameterError

---

## ScrImportSetOperations Tests

### Class Information
- **LCM Interface**: IScrImportSet
- **Purpose**: Manages import settings and mappings for scripture import (USFM, Paratext, etc.)
- **Children**: Mappings (IScrImportSet.MappingsOC), Book references
- **Key Properties**: ImportDomain, ImportTypeEnum, NoteTypeRA

### Test_Create_ImportSet

**Action**:
```python
import_set = project.ScrImportSets.Create(
    name="USFM Import",
    import_domain="Scripture"
)
```

**Verify**:
- `import_set is not None`
- `import_set.Name == "USFM Import"`
- Import set in project's import collection

### Test_Create_NullName

**Action**:
```python
import_set = project.ScrImportSets.Create(name=None)
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetName

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
```

**Action**:
```python
name = project.ScrImportSets.GetName(import_set)
```

**Verify**:
- `name == "Test Import"`

### Test_SetName

**Setup**:
```python
import_set = project.ScrImportSets.Create("Old Name")
```

**Action**:
```python
project.ScrImportSets.SetName(import_set, "New Name")
```

**Verify**:
- `project.ScrImportSets.GetName(import_set) == "New Name"`

### Test_AddMapping

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
```

**Action**:
```python
mapping = project.ScrImportSets.AddMapping(
    import_set,
    marker="\\p",
    style_name="Paragraph"
)
```

**Verify**:
- `mapping is not None`
- `mapping in import_set.MappingsOC`
- Mapping has correct marker and style

### Test_GetMappings

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
project.ScrImportSets.AddMapping(import_set, "\\p", "Paragraph")
project.ScrImportSets.AddMapping(import_set, "\\s", "Section Head")
```

**Action**:
```python
mappings = project.ScrImportSets.GetMappings(import_set)
```

**Verify**:
- `len(mappings) == 2`
- Both mappings present

### Test_Delete_ImportSet

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
import_set_guid = import_set.Guid
```

**Action**:
```python
project.ScrImportSets.Delete(import_set)
```

**Verify**:
- Import set removed from project
- Import set object no longer accessible by GUID

### Test_Delete_CascadeMappings

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
mapping = project.ScrImportSets.AddMapping(import_set, "\\p", "Paragraph")
mapping_guid = mapping.Guid
```

**Action**:
```python
project.ScrImportSets.Delete(import_set)
```

**Verify**:
- Mapping also deleted (cascade)
- Mapping no longer accessible by GUID

---

## ScrMarkerMappingOperations Tests

### Class Information
- **LCM Interface**: IScrMarkerMapping
- **Parent**: ScrImportSet (IScrImportSet.MappingsOC)
- **Purpose**: Maps USFM markers to FLEx paragraph styles
- **Key Properties**: BeginMarker (string), EndMarker (string), StyleName (string)

### Test_Create_Mapping

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
```

**Action**:
```python
mapping = project.ScrMarkerMappings.Create(
    import_set,
    begin_marker="\\p",
    style_name="Paragraph"
)
```

**Verify**:
- `mapping is not None`
- `mapping.Owner == import_set`
- `mapping in import_set.MappingsOC`
- `mapping.BeginMarker == "\\p"`
- `mapping.StyleName == "Paragraph"`

### Test_Create_WithEndMarker

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
```

**Action**:
```python
mapping = project.ScrMarkerMappings.Create(
    import_set,
    begin_marker="\\f",
    end_marker="\\f*",
    style_name="Footnote"
)
```

**Verify**:
- `mapping.BeginMarker == "\\f"`
- `mapping.EndMarker == "\\f*"`
- Paired marker mapping works

### Test_Create_NullImportSet

**Action**:
```python
mapping = project.ScrMarkerMappings.Create(None, "\\p", "Paragraph")
```

**Verify**:
- Raises FP_NullParameterError

### Test_Create_NullMarker

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
```

**Action**:
```python
mapping = project.ScrMarkerMappings.Create(import_set, None, "Paragraph")
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetBeginMarker

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
mapping = project.ScrMarkerMappings.Create(import_set, "\\p", "Paragraph")
```

**Action**:
```python
marker = project.ScrMarkerMappings.GetBeginMarker(mapping)
```

**Verify**:
- `marker == "\\p"`

### Test_SetBeginMarker

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
mapping = project.ScrMarkerMappings.Create(import_set, "\\p", "Paragraph")
```

**Action**:
```python
project.ScrMarkerMappings.SetBeginMarker(mapping, "\\q1")
```

**Verify**:
- `project.ScrMarkerMappings.GetBeginMarker(mapping) == "\\q1"`

### Test_GetStyleName

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
mapping = project.ScrMarkerMappings.Create(import_set, "\\p", "Paragraph")
```

**Action**:
```python
style = project.ScrMarkerMappings.GetStyleName(mapping)
```

**Verify**:
- `style == "Paragraph"`

### Test_SetStyleName

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
mapping = project.ScrMarkerMappings.Create(import_set, "\\p", "Paragraph")
```

**Action**:
```python
project.ScrMarkerMappings.SetStyleName(mapping, "Poetry")
```

**Verify**:
- `project.ScrMarkerMappings.GetStyleName(mapping) == "Poetry"`

### Test_Delete_Mapping

**Setup**:
```python
import_set = project.ScrImportSets.Create("Test Import")
mapping = project.ScrMarkerMappings.Create(import_set, "\\p", "Paragraph")
mapping_guid = mapping.Guid
```

**Action**:
```python
project.ScrMarkerMappings.Delete(mapping)
```

**Verify**:
- Mapping removed from import_set.MappingsOC
- Mapping no longer accessible by GUID

### Test_Integration_ImportSetWithMultipleMappings

**Setup**:
```python
import_set = project.ScrImportSets.Create("Full USFM Import")
```

**Action**:
```python
# Create common USFM mappings
p_map = project.ScrMarkerMappings.Create(import_set, "\\p", "Paragraph")
s_map = project.ScrMarkerMappings.Create(import_set, "\\s", "Section Head")
q1_map = project.ScrMarkerMappings.Create(import_set, "\\q1", "Poetry Line 1")
f_map = project.ScrMarkerMappings.Create(import_set, "\\f", "\\f*", "Footnote")
```

**Verify**:
- All 4 mappings in import_set.MappingsOC
- Each mapping has correct marker and style
- End marker set correctly for footnote mapping

---

## Integration Test Scenarios

### Scenario 1: Complete Scripture Book Creation

**Objective**: Create a full scripture book with sections and content.

**Steps**:
1. Create Genesis book (canonical 1)
2. Create section 1 with heading "Creation Account"
3. Add paragraph to section 1 with Genesis 1:1 text
4. Add paragraph to section 1 with Genesis 1:2 text
5. Create section 2 with heading "Light and Darkness"
6. Add paragraph to section 2 with Genesis 1:3-5 text
7. Verify hierarchy intact
8. Open in FLEx GUI and verify display

**Expected Results**:
- Book appears in scripture navigation
- Both sections display with correct headings
- Paragraphs display in correct order
- Hierarchy maintained: Book → Section → Paragraph

### Scenario 2: Scripture Import Mapping Workflow

**Objective**: Set up import mappings for USFM import.

**Steps**:
1. Create import set "USFM Genesis"
2. Add mappings for common markers:
   - `\p` → "Paragraph"
   - `\s` → "Section Head"
   - `\q1` → "Poetry Line 1"
   - `\f` / `\f*` → "Footnote"
3. Verify all mappings created
4. Test retrieval of mappings
5. Modify mapping styles
6. Delete one mapping
7. Verify cascade works

**Expected Results**:
- All mappings created successfully
- Mappings retrievable by marker
- Style modifications work
- Single mapping deletion doesn't affect others
- Import set deletion cascades to all mappings

### Scenario 3: Multi-Book Scripture Project

**Objective**: Create multiple books and verify ordering.

**Steps**:
1. Create Genesis (1)
2. Create Exodus (2)
3. Create Matthew (40)
4. Create John (43)
5. Verify GetAll() returns all 4 books
6. Verify books accessible by canonical number
7. Delete Exodus
8. Verify 3 books remain

**Expected Results**:
- All 4 books created
- GetAll() returns correct count
- Find() works for each canonical number
- Deletion removes only target book
- Remaining books intact after deletion

---

## Test Execution Notes

### Prerequisites
- Clean FLEx test project
- Write-enabled access
- Sufficient permissions for scripture data

### Common Setup
```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("TestProject_Scripture", writeEnabled=True)
```

### Common Teardown
```python
# Clean up created objects
# Close project
project.CloseProject()
```

### Known Issues
- Document any known issues discovered during testing
- Note workarounds if available
- Track in bug reports

### Test Data
- Use Genesis 1:1-5 for basic tests
- Use Psalm 23 for poetry/formatting tests
- Use Gospel passages for NT tests

---

## Test Status Summary

| Class | Tests Specified | Tests Implemented | Tests Passing | Coverage |
|-------|----------------|-------------------|---------------|----------|
| ScrBookOperations | 20 | 0 | 0 | 0% |
| ScrSectionOperations | 18 | 0 | 0 | 0% |
| ScrSectionHeadOperations | 5 | 0 | 0 | 0% |
| ScrBookRefOperations | 3 | 0 | 0 | 0% |
| ScrImportSetOperations | 10 | 0 | 0 | 0% |
| ScrMarkerMappingOperations | 12 | 0 | 0 | 0% |
| **Total** | **68** | **0** | **0** | **0%** |

---

## Next Steps

1. Implement test cases in Python unittest framework
2. Run tests against programmer agent's implementations
3. Document failures and file bug reports
4. Verify fixes and re-run tests
5. Achieve 100% pass rate before release

---

**Document Version**: 1.0
**Last Updated**: 2025-12-05
**Status**: Draft - Awaiting Implementation
