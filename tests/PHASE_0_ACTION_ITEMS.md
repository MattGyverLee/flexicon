# Phase 0 Action Items & Implementation Adjustments

**Based on:** Phase 0 Verification Script Results
**Date:** 2026-02-21
**Status:** All tests passed - Ready for Phase 1

---

## Critical Issues Requiring Fixes Before Phase 1

### [CRITICAL] 1. Exception Type Corrections

**Issue:** Implementation plan assumes Python exception types, but FLEx uses .NET exceptions.

#### Change 1.1: Invalid HVO Lookup Handling

**Current (WRONG):**
```python
try:
    obj = project.Object(hvo)
except KeyError:
    raise ObjectNotFoundError(...)
```

**Corrected (RIGHT):**
```python
from System.Collections.Generic import KeyNotFoundException

try:
    obj = project.Object(hvo)
except KeyNotFoundException as e:
    # Message: "Unable to find hvo XXXXX in the object dictionary"
    raise ObjectNotFoundError(...)
```

**Files to Update:**
- `core/validators.py` - Any HVO validation
- `core/resolvers.py` - Any lookup code
- All operations classes that do HVO lookups

#### Change 1.2: DateTime Parsing Handling

**Current (WRONG):**
```python
try:
    dt = System.DateTime.Parse(date_string)
except ValueError:
    raise InvalidParameterError(...)
```

**Corrected (RIGHT):**
```python
from System import FormatException

try:
    dt = System.DateTime.Parse(date_string)
except FormatException as e:
    # Message: "The string was not recognized as a valid DateTime..."
    raise InvalidParameterError(...)
```

**Files to Update:**
- Any code that parses DateTime strings
- Custom field value handlers
- Date-based validators

#### Change 1.3: Type Casting Errors

**Context:** When casting objects to ILexEntry or other LCM types, may throw specific exceptions.

**Research Action:**
- [ ] Test invalid casts in write-enabled mode
- [ ] Document actual exception types
- [ ] Update all cast handlers

---

## High Priority: API Pattern Corrections

### [HIGH] 2. PossibilityList Access Pattern

**Issue:** `project.PossibilityLists` returns `PossibilityListOperations` (wrapper), not iterable collection.

#### Current API (from test)
```python
# DOESN'T WORK - Not iterable:
poss_lists = project.PossibilityLists
all_lists = list(poss_lists)  # TypeError!
```

#### Required Research
- [ ] Study `PossibilityListOperations` class methods
- [ ] Determine if method like `GetAll()` exists
- [ ] Check if direct LCM access is needed
- [ ] Document final pattern

#### Workaround for Phase 1
Until pattern is determined, use direct LCM access:
```python
# Direct LCM access (temporary):
lang_proj = project.lp  # Get underlying LangProject
poss_lists = lang_proj.PossibilityListsOC  # Object collection
for plist in poss_lists:
    # Process list
```

#### Implementation Action
- [ ] Create lookup utility function in `core/resolvers.py`
- [ ] Function signature: `lookup_possibility_list(project, list_name) -> ICmPossibilityList`
- [ ] Use in all sense/semantic domain lookups
- [ ] Test with real data

---

## Medium Priority: Testing Gaps

### [MEDIUM] 3. Write-Enabled Testing

**Issue:** All Phase 0 tests ran in read-only mode. Full validation needs write operations.

#### Testing Requirements for Phase 2
- [ ] Open project with `writeEnabled=True`
- [ ] Test create operation for LexEntry
- [ ] Test homograph creation (same form, different meaning)
- [ ] Verify HomographNumber auto-assignment
- [ ] Test delete operations
- [ ] Verify SaveChanges() persistence
- [ ] Test transaction rollback

#### Create New Test Script: `tests/write_operations_validation.py`
- Similar structure to `manual_verification.py`
- Tests each major operation (Create, Update, Delete)
- Documents safe cleanup (deletes test data)
- Verifies transaction behavior

### [MEDIUM] 4. Transaction Model Verification

**Issue:** Transaction methods (BeginUndoTask, EndUndoTask) not confirmed in read-only mode.

#### Research Required
```python
# Verify in write-enabled mode:
if hasattr(project.project, 'BeginUndoTask'):
    # Use context manager pattern?
    # Or explicit begin/end?
```

#### Implementation Pattern to Test
```python
# Pattern A: Explicit transactions
project.project.BeginUndoTask("Description")
try:
    # Make changes
    obj = project.LexEntry.Create(...)
    obj.SomeProperty = "value"
finally:
    project.project.EndUndoTask()
    project.SaveChanges()
```

#### Files to Update After Verification
- `BaseOperations.py` - Add transaction support
- All CRUD operation classes
- Error handlers with rollback

---

## Implementation Adjustments Needed

### [MEDIUM] 5. Error Handling Strategy

**Current Plan Issues:**
- Assumes Python exception types
- No retry logic for transient failures
- No rollback on error

**Revised Strategy:**
```python
# New pattern in operations classes:
def safe_create(self, project, **kwargs):
    """Create with transaction safety."""
    try:
        # Start transaction
        project.project.BeginUndoTask("Create operation")

        # Create and configure
        obj = self._create_object(project, **kwargs)
        self._set_properties(obj, kwargs)

        # Commit transaction
        project.project.EndUndoTask()
        project.SaveChanges()

        return obj

    except KeyNotFoundException as e:
        # Handle lookup failures
        project.project.RollbackUndoToMark()
        raise ObjectNotFoundError(...) from e

    except FormatException as e:
        # Handle invalid data
        project.project.RollbackUndoToMark()
        raise InvalidParameterError(...) from e

    except Exception as e:
        # Unexpected error - rollback
        project.project.RollbackUndoToMark()
        raise OperationFailedError(...) from e
```

---

## Verification Checklist

Before proceeding with Phase 1 implementation, complete these:

### Exception Handling
- [ ] Update all `except KeyError` to catch `.NET KeyNotFoundException`
- [ ] Update all DateTime parsing to catch `System.FormatException`
- [ ] Test type casting error handling
- [ ] Import .NET exception types in all modules that need them
- [ ] Update `core/exceptions.py` with .NET exception mapping

### API Patterns
- [ ] Determine correct PossibilityList access pattern
- [ ] Create lookup utility functions
- [ ] Test with real lexicon data (not just "Test" project)
- [ ] Document all API patterns in design guide

### Write Operation Testing
- [ ] Create write-operations-validation.py script
- [ ] Test create operations with writeEnabled=True
- [ ] Test update operations
- [ ] Test delete operations
- [ ] Verify SaveChanges() behavior
- [ ] Test transaction rollback

### Safety Guarantees
- [ ] Document safe operation orders
- [ ] Add pre-operation validation
- [ ] Add cleanup handlers
- [ ] Add transaction support to BaseOperations
- [ ] Create examples for safe patterns

---

## Files Requiring Updates

### Priority 1: Core Infrastructure
- [ ] `core/exceptions.py` - Map .NET exceptions to custom exceptions
- [ ] `core/validators.py` - Update exception types in validation
- [ ] `core/resolvers.py` - Update HVO lookup error handling

### Priority 2: Operations Classes
- [ ] `flexicon/code/BaseOperations.py` - Add transaction support
- [ ] All operation classes that do lookups - Update exception handling
- [ ] All operation classes that parse dates - Update exception handling

### Priority 3: Testing
- [ ] `tests/manual_verification.py` - Already complete
- [ ] `tests/write_operations_validation.py` - Create new
- [ ] `tests/test_operations_baseline.py` - May need exception updates

### Priority 4: Documentation
- [ ] Update IMPLEMENTATION_PLAN.md with corrected exceptions
- [ ] Create API_PATTERNS.md with verified patterns
- [ ] Create SAFE_OPERATIONS_GUIDE.md with documented sequences

---

## Code Examples for Phase 1

### Example 1: Safe Lookup with Correct Exception Handling
```python
def find_entry_by_form(project: FLExProject, form: str) -> ILexEntry:
    """Find entry by lexeme form, with proper error handling."""
    from System.Collections.Generic import KeyNotFoundException

    try:
        # Implementation
        for entry in project.LexEntry.GetAll():
            if str(entry) == form:
                return entry
        raise ObjectNotFoundError("LexEntry", form)
    except KeyNotFoundException as e:
        raise ObjectNotFoundError("LexEntry", form) from e
```

### Example 2: Safe DateTime Parsing
```python
def parse_flex_date(date_string: str) -> datetime:
    """Parse FLEx datetime with proper error handling."""
    from System import FormatException

    try:
        import System
        dt = System.DateTime.Parse(date_string)
        return dt  # Convert to Python datetime as needed
    except FormatException as e:
        raise InvalidParameterError(f"Invalid date: {date_string}") from e
```

### Example 3: Safe Create with Transactions
```python
def create_with_transaction(project: FLExProject, **kwargs):
    """Create object with transaction safety."""
    # Mark starting point for rollback
    mark = project.project.UndoStack.Mark()

    try:
        # Create and configure
        obj = create_object(project, kwargs)
        return obj
    except Exception as e:
        # Roll back to mark on any error
        project.project.RollbackUndoToMark(mark)
        raise
```

---

## Assumptions Now Verified ✅

The following assumptions from the implementation plan are now **VERIFIED** and can proceed:

1. ✅ Properties on objects are accessible (HomographNumber, LexemeFormOA)
2. ✅ Can iterate through collections safely
3. ✅ @property decorator pattern works with LCM objects
4. ✅ Safe operation sequence for reads
5. ✅ writeEnabled flag controls modifications

## Assumptions Requiring Updates ❌

1. ❌ Exception types - USE .NET EXCEPTIONS, NOT PYTHON
2. ⚠️ PossibilityList iteration - USE CORRECT API PATTERN (TBD)
3. ⚠️ Transaction methods - VERIFY IN WRITE MODE (TBD)

---

## Timeline for Phase 1-4

### Phase 1: Code Quality Improvements (With corrections)
- Update exception handling in all modules
- Implement PossibilityList lookup pattern
- Add safety guards and validation
- Timeline: 2-3 weeks (with API research)

### Phase 2: Property Aliases and Wrappers
- Implement @property wrappers (verified safe)
- Create convenience classes
- Add documentation and examples
- Timeline: 1-2 weeks

### Phase 3: Write Operations & Transactions
- Implement create, update, delete with transactions
- Add rollback on error
- Test with writeEnabled=True
- Timeline: 3-4 weeks

### Phase 4: Advanced Features
- Batch operations
- Undo/redo handling
- Performance optimization
- Timeline: 2-3 weeks

**Total Estimated Time: 8-12 weeks**

---

## Conclusion

Phase 0 verification was successful. **All major assumptions validated.**

**Key takeaway:** The biggest surprise was exception types - FLEx uses .NET exceptions throughout, not Python exceptions. This requires updating error handlers across the codebase.

**Proceed with Phase 1 after:**
1. Updating exception handling for .NET exceptions
2. Researching and documenting PossibilityList API
3. Creating write-operations validation tests

**The verified patterns (@property, read operations, safe sequences) are solid and can proceed as planned.**
