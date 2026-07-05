# Lists Domain Consolidation Template

## Overview
This document provides a step-by-step template for refactoring the remaining 4 operations files (AgentOperations, TranslationTypeOperations, OverlayOperations, PublicationOperations) to inherit from `PossibilityItemOperations` base class.

## Refactoring Pattern (3 Steps)

### Step 1: Update Class Definition & Imports
**OLD:**
```python
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

class AgentOperations(BaseOperations):
    ...
    def __init__(self, project):
        super().__init__(project)

    def _GetSequence(self, parent):
        return parent.SubPossibilitiesOS
```

**NEW:**
```python
from ..BaseOperations import OperationsMethod
from .possibility_item_base import PossibilityItemOperations

class AgentOperations(PossibilityItemOperations):
    ...
    def __init__(self, project):
        super().__init__(project)

    def _get_item_class_name(self):
        return "Agent"

    def _get_list_object(self):
        return self.project.lp.AnalyzingAgentsOC
```

### Step 2: Remove Shared CRUD Methods
**DELETE these methods entirely** (inherited from base class):
- GetAll()
- Create()
- Delete()
- Find()
- Exists()
- Duplicate()
- GetName() / SetName()
- GetDescription() / SetDescription()
- CompareTo()
- GetGuid()
- GetSyncableProperties()

**ALSO DELETE:**
- `_GetSequence()` method (base implements this)
- Private helper methods: `__ResolveObject()`, `__WSHandle()`, `__WSHandleAnalysis()`

### Step 3: Update Domain-Specific Methods
For methods that call the deleted private helpers, use Python name mangling to call parent's private methods:

**OLD (in domain-specific method):**
```python
agent = self.__ResolveObject(agent_or_hvo)
wsHandle = self.__WSHandle(wsHandle)
```

**NEW:**
```python
agent = self._PossibilityItemOperations__ResolveObject(agent_or_hvo)
wsHandle = self._PossibilityItemOperations__WSHandle(wsHandle)
```

Note: Check if method uses `__WSHandle` or `__WSHandleAnalysis` - the base class has `__WSHandle` only, so `__WSHandleAnalysis` needs special handling or custom implementation in domain-specific sections.

## File-Specific Details

### AgentOperations
- Domain Start Line: 599
- Item Class Name: "Agent"
- List Object: `self.project.lp.AnalyzingAgentsOC`
- Domain Methods to Keep: CreateHumanAgent, CreateParserAgent, GetVersion, SetVersion, IsHuman, IsParser, GetHuman, SetHuman, GetEvaluations, GetEvaluationCount, FindByType, GetHumanAgents, GetParserAgents, GetDateCreated, GetDateModified
- Special Note: Use `__WSHandleAnalysis` - keep as custom or implement locally

### TranslationTypeOperations
- Domain Start Line: 522
- Item Class Name: "TranslationType"
- List Object: `self.project.lp.TranslationTagsOA`
- Domain Methods: GetAbbreviation, SetAbbreviation, GetAnalysisWS, SetAnalysisWS, GetTextsWithType, GetSegmentsWithType, GetFreeTranslationType, GetLiteralTranslationType, GetBackTranslationType, FindByWS, IsDefault, SetDefault
- Special Note: Uses System.Guid for predefined type checks

### OverlayOperations
- Domain Start Line: 626
- Item Class Name: "Overlay"
- List Object: `None` (special case - chart-scoped, GetAll() needs override)
- Domain Methods: IsVisible, SetVisible, GetDisplayOrder, SetDisplayOrder, GetElements, AddElement, RemoveElement, GetChart, GetPossItems, FindByChart, GetVisibleOverlays
- Special Note: Chart-scoped operations, may need custom GetAll() override

### PublicationOperations
- Domain Start Line: 579
- Item Class Name: "Publication"
- List Object: `self.project.lexDB.PublicationTypesOA`
- Domain Methods: GetPageLayout, SetPageLayout, GetIsDefault, SetIsDefault, GetPageHeight, SetPageHeight, GetPageWidth, SetPageWidth, GetDivisions, AddDivision, GetHeaderFooter, GetIsLandscape, GetSubPublications, GetParent, GetDateCreated, GetDateModified
- Special Note: Uses System.DateTime, nested publication handling

## Implementation Checklist

For each file:
- [ ] Update class definition and imports
- [ ] Add `_get_item_class_name()` method
- [ ] Add `_get_list_object()` method
- [ ] Remove all shared CRUD methods
- [ ] Remove `_GetSequence()` method
- [ ] Remove private helper methods
- [ ] Update method calls to use parent's private methods via name mangling
- [ ] Verify syntax: `python -m py_compile filename.py`
- [ ] Commit with message format: "Consolidate: Refactor {FileName} to inherit from PossibilityItemOperations base class"

## Expected Results

| File | Before | After | Savings |
|------|--------|-------|---------|
| AgentOperations | 1,316 | ~400 | ~920 LOC |
| TranslationTypeOperations | 1,234 | ~400 | ~840 LOC |
| OverlayOperations | 1,437 | ~500 | ~940 LOC |
| PublicationOperations | 1,623 | ~500 | ~1,120 LOC |
| **TOTAL** | **5,610** | **~1,800** | **~3,820 LOC** |

## Estimated Consolidation
- **Base Class Only**: 767 LOC (possibility_item_base.py + refactored ConfidenceOperations)
- **Remaining 4 Files**: ~3,820 LOC
- **GRAND TOTAL**: ~4,587 LOC consolidation for GROUP 8

---

**Template Version**: 1.0
**Created**: 2026-04-06
**Status**: Ready for implementation
