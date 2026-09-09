# Discourse Operations Test Specifications

## Overview

This document provides detailed test specifications for all 6 Discourse Operations classes in flexicon. These classes handle discourse analysis, constituent charts, chart rows, word groups, and discourse markers.

**Test Scope**: 6 Discourse Operations classes
**Related Classes**: TextOperations, SegmentOperations, ParagraphOperations

---

## Table of Contents

1. [ConstituentChartOperations Tests](#constituentchartoperations-tests)
2. [ChartRowOperations Tests](#chartrowoperations-tests)
3. [WordGroupOperations Tests](#wordgroupoperations-tests)
4. [MovedTextMarkerOperations Tests](#movedtextmarkeroperations-tests)
5. [ClauseMarkerOperations Tests](#clausemarkeroperations-tests)
6. [ChartTemplateOperations Tests](#charttemplateoperations-tests)

---

## ConstituentChartOperations Tests

### Class Information
- **LCM Interface**: IDsConstChart
- **Parent**: Text (IText.ChartsOC) or DiscourseData
- **Children**: Rows (IDsConstChart.RowsOS), Templates
- **Key Properties**: BasedOnRA (IText), Name (MultiUnicode), TemplateRA

### Test_Create_MinimalChart

**Setup**:
```python
project = FLExProject()
project.OpenProject("TestProject", writeEnabled=True)
# Create or get a text
text = project.Texts.Create("Sample Text for Charting")
```

**Action**:
```python
chart = project.Charts.Create(text, name="Main Chart")
```

**Verify**:
- `chart is not None`
- `chart.BasedOnRA == text`
- `chart.Name == "Main Chart"`
- `chart.RowsOS.Count == 0` (no rows yet)
- `chart.Guid != System.Guid.Empty`
- Chart in text's ChartsOC collection

**Cleanup**:
```python
project.Charts.Delete(chart)
project.CloseProject()
```

### Test_Create_ChartWithTemplate

**Setup**:
```python
text = project.Texts.Create("Test Text")
template = project.ChartTemplates.Create("Standard Template")
```

**Action**:
```python
chart = project.Charts.Create(
    text,
    name="Templated Chart",
    template=template
)
```

**Verify**:
- `chart.TemplateRA == template`
- Chart initialized with template properties

### Test_Create_NullText

**Action**:
```python
chart = project.Charts.Create(None, "Test Chart")
```

**Verify**:
- Raises FP_NullParameterError

### Test_Create_NullName

**Setup**:
```python
text = project.Texts.Create("Test Text")
```

**Action**:
```python
chart = project.Charts.Create(text, name=None)
```

**Verify**:
- Either: Raises FP_NullParameterError
- Or: Creates chart with empty name (document behavior)

### Test_Create_ReadOnlyProject

**Setup**:
```python
project.OpenProject("TestProject", writeEnabled=False)
text = list(project.Texts.GetAll())[0]
```

**Action**:
```python
chart = project.Charts.Create(text, "Test")
```

**Verify**:
- Raises FP_ReadOnlyError

### Test_Find_ExistingChart

**Setup**:
```python
text = project.Texts.Create("Test Text")
created_chart = project.Charts.Create(text, "Find Me")
```

**Action**:
```python
found_chart = project.Charts.Find(text, "Find Me")
```

**Verify**:
- `found_chart is not None`
- `found_chart.Hvo == created_chart.Hvo`
- `found_chart.Name == "Find Me"`

### Test_Find_NonExistentChart

**Setup**:
```python
text = project.Texts.Create("Test Text")
```

**Action**:
```python
found_chart = project.Charts.Find(text, "Doesn't Exist")
```

**Verify**:
- `found_chart is None` (returns None, not exception)

### Test_GetAll_ForText

**Setup**:
```python
text = project.Texts.Create("Test Text")
project.Charts.Create(text, "Chart 1")
project.Charts.Create(text, "Chart 2")
```

**Action**:
```python
charts = list(project.Charts.GetAll(text))
```

**Verify**:
- `len(charts) == 2`
- Both charts present

### Test_GetAll_Empty

**Setup**:
```python
text = project.Texts.Create("Empty Text")
```

**Action**:
```python
charts = list(project.Charts.GetAll(text))
```

**Verify**:
- `len(charts) == 0`
- Returns empty iterator (not None)

### Test_Delete_ExistingChart

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Delete Me")
chart_guid = chart.Guid
```

**Action**:
```python
project.Charts.Delete(chart)
```

**Verify**:
- Chart removed from text.ChartsOC
- Chart object no longer accessible by GUID

### Test_Delete_CascadeRows

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
row_guid = row.Guid
```

**Action**:
```python
project.Charts.Delete(chart)
```

**Verify**:
- Row also deleted (cascade)
- Row object no longer accessible by GUID

### Test_GetName

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
```

**Action**:
```python
name = project.Charts.GetName(chart)
```

**Verify**:
- `name == "Test Chart"`

### Test_SetName

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Old Name")
```

**Action**:
```python
project.Charts.SetName(chart, "New Name")
```

**Verify**:
- `project.Charts.GetName(chart) == "New Name"`

### Test_GetText

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
```

**Action**:
```python
retrieved_text = project.Charts.GetText(chart)
```

**Verify**:
- `retrieved_text.Hvo == text.Hvo`
- Correct text reference

### Test_GetRowCount

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
project.ChartRows.Create(chart)
project.ChartRows.Create(chart)
```

**Action**:
```python
count = project.Charts.GetRowCount(chart)
```

**Verify**:
- `count == 2`

### Test_GetRows

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row1 = project.ChartRows.Create(chart)
row2 = project.ChartRows.Create(chart)
```

**Action**:
```python
rows = project.Charts.GetRows(chart)
```

**Verify**:
- `len(rows) == 2`
- Rows in correct order

### Test_Integration_TextChartRowHierarchy

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
```

**Verify**:
- `chart.BasedOnRA == text`
- `row.Owner == chart`
- `chart in text.ChartsOC`
- `row in chart.RowsOS`
- Full hierarchy intact

---

## ChartRowOperations Tests

### Class Information
- **LCM Interface**: IConstChartRow
- **Parent**: Chart (IDsConstChart.RowsOS)
- **Children**: Cells (cells contain word groups, markers)
- **Key Properties**: Label (MultiUnicode), ClauseType, EndParagraph, EndSentence

### Test_Create_MinimalRow

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
```

**Action**:
```python
row = project.ChartRows.Create(chart)
```

**Verify**:
- `row is not None`
- `row.Owner == chart`
- `row in chart.RowsOS`
- `row.Guid != System.Guid.Empty`

### Test_Create_RowWithLabel

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
```

**Action**:
```python
row = project.ChartRows.Create(chart, label="Row 1")
```

**Verify**:
- `project.ChartRows.GetLabel(row) == "Row 1"`

### Test_Create_NullChart

**Action**:
```python
row = project.ChartRows.Create(None)
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetLabel

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart, label="Test Row")
```

**Action**:
```python
label = project.ChartRows.GetLabel(row)
```

**Verify**:
- `label == "Test Row"`

### Test_SetLabel

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart, label="Old Label")
```

**Action**:
```python
project.ChartRows.SetLabel(row, "New Label")
```

**Verify**:
- `project.ChartRows.GetLabel(row) == "New Label"`

### Test_GetChart

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
```

**Action**:
```python
retrieved_chart = project.ChartRows.GetChart(row)
```

**Verify**:
- `retrieved_chart.Hvo == chart.Hvo`

### Test_Delete_ExistingRow

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
row_guid = row.Guid
```

**Action**:
```python
project.ChartRows.Delete(row)
```

**Verify**:
- Row removed from chart.RowsOS
- Row object no longer accessible by GUID

### Test_Delete_CascadeWordGroups

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
# Assume word group can be added to row
wordgroup = project.WordGroups.Create(row, cell_index=0)
wg_guid = wordgroup.Guid
```

**Action**:
```python
project.ChartRows.Delete(row)
```

**Verify**:
- Word group also deleted (cascade)
- Word group no longer accessible by GUID

### Test_GetEndParagraph

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
```

**Action**:
```python
project.ChartRows.SetEndParagraph(row, True)
end_para = project.ChartRows.GetEndParagraph(row)
```

**Verify**:
- `end_para == True`

### Test_GetEndSentence

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
```

**Action**:
```python
project.ChartRows.SetEndSentence(row, True)
end_sent = project.ChartRows.GetEndSentence(row)
```

**Verify**:
- `end_sent == True`

---

## WordGroupOperations Tests

### Class Information
- **LCM Interface**: IConstChartWordGroup
- **Parent**: Chart row (contained in cells)
- **Key Properties**: BeginSegmentRA, EndSegmentRA, BeginAnalysisIndex, EndAnalysisIndex
- **Purpose**: Links discourse chart to actual text segments

### Test_Create_WordGroup

**Setup**:
```python
# Create text with segments
text = project.Texts.Create("Test Text")
# Add paragraph and segment
para = project.Paragraphs.Create(text.ContentsOA, "This is a test sentence.")
segment = para.SegmentsOS[0]  # Assuming segmentation

chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
```

**Action**:
```python
wordgroup = project.WordGroups.Create(
    row,
    cell_index=0,
    begin_segment=segment
)
```

**Verify**:
- `wordgroup is not None`
- `wordgroup.BeginSegmentRA == segment`
- Word group properly linked to segment

### Test_Create_WithEndSegment

**Setup**:
```python
text = project.Texts.Create("Test Text")
para = project.Paragraphs.Create(text.ContentsOA, "First sentence. Second sentence.")
segment1 = para.SegmentsOS[0]
segment2 = para.SegmentsOS[1]

chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
```

**Action**:
```python
wordgroup = project.WordGroups.Create(
    row,
    cell_index=0,
    begin_segment=segment1,
    end_segment=segment2
)
```

**Verify**:
- `wordgroup.BeginSegmentRA == segment1`
- `wordgroup.EndSegmentRA == segment2`
- Word group spans multiple segments

### Test_GetBeginSegment

**Setup**:
```python
# Setup with word group
wordgroup = ... # created in previous test
segment = ...
```

**Action**:
```python
begin_seg = project.WordGroups.GetBeginSegment(wordgroup)
```

**Verify**:
- `begin_seg.Hvo == segment.Hvo`

### Test_SetBeginSegment

**Action**:
```python
project.WordGroups.SetBeginSegment(wordgroup, new_segment)
```

**Verify**:
- `wordgroup.BeginSegmentRA == new_segment`

### Test_GetEndSegment

**Action**:
```python
end_seg = project.WordGroups.GetEndSegment(wordgroup)
```

**Verify**:
- Returns correct segment or None

### Test_Delete_WordGroup

**Setup**:
```python
# Create word group
wordgroup = project.WordGroups.Create(row, 0, segment)
wg_guid = wordgroup.Guid
```

**Action**:
```python
project.WordGroups.Delete(wordgroup)
```

**Verify**:
- Word group removed from chart structure
- Word group no longer accessible by GUID
- Referenced segment still exists (not cascade deleted)

### Test_Integration_ChartRowWordGroupSegmentLink

**Setup**:
```python
text = project.Texts.Create("Test Text")
para = project.Paragraphs.Create(text.ContentsOA, "Test sentence.")
segment = para.SegmentsOS[0]

chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
wordgroup = project.WordGroups.Create(row, 0, segment)
```

**Verify**:
- `chart.BasedOnRA == text`
- `wordgroup.BeginSegmentRA == segment`
- Chart links correctly to text structure
- Segment accessible from word group

---

## MovedTextMarkerOperations Tests

### Class Information
- **LCM Interface**: IConstChartMovedTextMarker
- **Purpose**: Marks text that has been moved in discourse structure (discontinuous elements)
- **Key Properties**: WordGroup (reference), Preposed (bool)

### Test_Create_MovedTextMarker

**Setup**:
```python
# Create chart with word group
text = project.Texts.Create("Test Text")
para = project.Paragraphs.Create(text.ContentsOA, "Test sentence.")
segment = para.SegmentsOS[0]

chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
wordgroup = project.WordGroups.Create(row, 0, segment)
```

**Action**:
```python
marker = project.MovedTextMarkers.Create(
    wordgroup,
    preposed=True
)
```

**Verify**:
- `marker is not None`
- `marker.WordGroup == wordgroup`
- `marker.Preposed == True`

### Test_Create_PostposedMarker

**Action**:
```python
marker = project.MovedTextMarkers.Create(
    wordgroup,
    preposed=False
)
```

**Verify**:
- `marker.Preposed == False`

### Test_GetPreposed

**Setup**:
```python
marker = project.MovedTextMarkers.Create(wordgroup, preposed=True)
```

**Action**:
```python
is_preposed = project.MovedTextMarkers.GetPreposed(marker)
```

**Verify**:
- `is_preposed == True`

### Test_SetPreposed

**Action**:
```python
project.MovedTextMarkers.SetPreposed(marker, False)
```

**Verify**:
- `project.MovedTextMarkers.GetPreposed(marker) == False`

### Test_GetWordGroup

**Action**:
```python
wg = project.MovedTextMarkers.GetWordGroup(marker)
```

**Verify**:
- `wg.Hvo == wordgroup.Hvo`

### Test_Delete_Marker

**Setup**:
```python
marker = project.MovedTextMarkers.Create(wordgroup, preposed=True)
marker_guid = marker.Guid
```

**Action**:
```python
project.MovedTextMarkers.Delete(marker)
```

**Verify**:
- Marker removed from chart
- Marker no longer accessible by GUID
- Word group still exists (not cascade deleted)

---

## ClauseMarkerOperations Tests

### Class Information
- **LCM Interface**: IConstChartClauseMarker
- **Purpose**: Marks clause boundaries and types in discourse analysis
- **Key Properties**: DependentClauseType, ClauseType

### Test_Create_ClauseMarker

**Setup**:
```python
text = project.Texts.Create("Test Text")
chart = project.Charts.Create(text, "Test Chart")
row = project.ChartRows.Create(chart)
```

**Action**:
```python
marker = project.ClauseMarkers.Create(row, cell_index=0)
```

**Verify**:
- `marker is not None`
- Marker associated with row
- Marker in correct cell

### Test_Create_WithClauseType

**Action**:
```python
# Assuming clause type possibilities exist
clause_type = ... # Get from project possibilities
marker = project.ClauseMarkers.Create(
    row,
    cell_index=0,
    clause_type=clause_type
)
```

**Verify**:
- `marker.ClauseType == clause_type`

### Test_GetClauseType

**Setup**:
```python
marker = project.ClauseMarkers.Create(row, 0, clause_type)
```

**Action**:
```python
ct = project.ClauseMarkers.GetClauseType(marker)
```

**Verify**:
- `ct.Hvo == clause_type.Hvo`

### Test_SetClauseType

**Action**:
```python
project.ClauseMarkers.SetClauseType(marker, new_clause_type)
```

**Verify**:
- `project.ClauseMarkers.GetClauseType(marker) == new_clause_type`

### Test_Delete_Marker

**Setup**:
```python
marker = project.ClauseMarkers.Create(row, 0)
marker_guid = marker.Guid
```

**Action**:
```python
project.ClauseMarkers.Delete(marker)
```

**Verify**:
- Marker removed from chart
- Marker no longer accessible by GUID

---

## ChartTemplateOperations Tests

### Class Information
- **LCM Interface**: IDsChartTemplate (or ICmPossibility)
- **Purpose**: Provides templates for creating consistent chart structures
- **Key Properties**: Name, Columns (column definitions)

### Test_Create_Template

**Action**:
```python
template = project.ChartTemplates.Create(
    name="Standard Constituent Chart"
)
```

**Verify**:
- `template is not None`
- `project.ChartTemplates.GetName(template) == "Standard Constituent Chart"`

### Test_Create_NullName

**Action**:
```python
template = project.ChartTemplates.Create(name=None)
```

**Verify**:
- Raises FP_NullParameterError

### Test_GetName

**Setup**:
```python
template = project.ChartTemplates.Create("Test Template")
```

**Action**:
```python
name = project.ChartTemplates.GetName(template)
```

**Verify**:
- `name == "Test Template"`

### Test_SetName

**Action**:
```python
project.ChartTemplates.SetName(template, "New Name")
```

**Verify**:
- `project.ChartTemplates.GetName(template) == "New Name"`

### Test_GetAll

**Setup**:
```python
project.ChartTemplates.Create("Template 1")
project.ChartTemplates.Create("Template 2")
```

**Action**:
```python
templates = list(project.ChartTemplates.GetAll())
```

**Verify**:
- `len(templates) >= 2`
- Created templates in collection

### Test_Delete_Template

**Setup**:
```python
template = project.ChartTemplates.Create("Delete Me")
template_guid = template.Guid
```

**Action**:
```python
project.ChartTemplates.Delete(template)
```

**Verify**:
- Template removed from project
- Template no longer accessible by GUID

### Test_Integration_ChartWithTemplate

**Setup**:
```python
text = project.Texts.Create("Test Text")
template = project.ChartTemplates.Create("Standard Template")
```

**Action**:
```python
chart = project.Charts.Create(text, "Templated Chart", template=template)
```

**Verify**:
- `chart.TemplateRA == template`
- Chart uses template structure

---

## Integration Test Scenarios

### Scenario 1: Complete Discourse Chart Creation

**Objective**: Create a full discourse chart with rows and word groups.

**Steps**:
1. Create text with 3-4 sentences
2. Create constituent chart for text
3. Create first row
4. Create second row
5. Add word group to first row (links to segment 1)
6. Add word group to second row (links to segment 2)
7. Add moved text marker to show discontinuous element
8. Verify structure in FLEx GUI

**Expected Results**:
- Chart displays in discourse view
- Rows appear in correct order
- Word groups link correctly to text
- Moved text marker shows displacement
- Full hierarchy intact

### Scenario 2: Complex Chart with Multiple Markers

**Objective**: Test chart with various marker types.

**Steps**:
1. Create text and chart
2. Create 5 rows
3. Add word groups to rows (linking to text segments)
4. Add moved text marker (preposed)
5. Add clause markers to show clause boundaries
6. Delete middle row
7. Verify cascade deletion of row contents

**Expected Results**:
- All markers created successfully
- Markers display correctly
- Row deletion cascades to contained elements
- Remaining rows and markers intact

### Scenario 3: Template-Based Chart Creation

**Objective**: Use templates for consistent chart creation.

**Steps**:
1. Create chart template "Standard Analysis"
2. Define template columns/structure
3. Create chart 1 using template
4. Create chart 2 using same template
5. Verify both charts use template structure
6. Modify template
7. Check if existing charts update (or not)

**Expected Results**:
- Template creates consistent structure
- Multiple charts can use same template
- Template modifications handled appropriately

---

## Test Execution Notes

### Prerequisites
- FLEx test project with texts
- Texts must have segmentation (for word groups)
- Write-enabled access

### Common Setup
```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("TestProject_Discourse", writeEnabled=True)

# Create test text with segments
text = project.Texts.Create("Discourse Test Text")
para = project.Paragraphs.Create(
    text.ContentsOA,
    "This is sentence one. This is sentence two. This is sentence three."
)
# Trigger segmentation if needed
```

### Common Teardown
```python
# Clean up
project.CloseProject()
```

### Test Data
- Use simple texts with clear clause boundaries
- 3-5 sentences per text
- Clear discourse structure (narrative, dialog, etc.)

---

## Test Status Summary

| Class | Tests Specified | Tests Implemented | Tests Passing | Coverage |
|-------|----------------|-------------------|---------------|----------|
| ConstituentChartOperations | 18 | 0 | 0 | 0% |
| ChartRowOperations | 11 | 0 | 0 | 0% |
| WordGroupOperations | 8 | 0 | 0 | 0% |
| MovedTextMarkerOperations | 7 | 0 | 0 | 0% |
| ClauseMarkerOperations | 6 | 0 | 0 | 0% |
| ChartTemplateOperations | 8 | 0 | 0 | 0% |
| **Total** | **58** | **0** | **0** | **0%** |

---

**Document Version**: 1.0
**Last Updated**: 2025-12-05
**Status**: Draft - Awaiting Implementation
