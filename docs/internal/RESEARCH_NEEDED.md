# Research Needed: Phase 2 Undo Stack Implementation

## Overview

Phase 1 (rollback transactions) is implemented and ready. Phase 2 (full undo stack integration) is **gated by research** - we must verify the LCM APIs before proceeding.

This document tracks what must be verified and by whom.

---

## What's Needed for Phase 2

Phase 2 requires exposing FLEx's full undo/redo stack so operations appear in FLEx's Ctrl+Z menu:

```python
# Phase 2 (future):
project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True, undoable=True)

with project.UndoableOperation("Add entry 'run'"):
    project.LexEntry.Create("run", "stem")

project.Undo()   # Reverses in FLEx Ctrl+Z
project.Redo()   # Reapplies
```

For this to work, the underlying LCM APIs must:
1. **Exist** with expected names
2. **Work correctly** in a real FLEx project
3. **Coexist** with the current `BeginNonUndoableTask()` session model

---

## Research Checklist

### Question 1: Does BeginUndoTask Exist?

**What to test:**
```python
from flexlibs2 import FLExProject
project = FLExProject()
project.OpenProject("TestProject", writeEnabled=True)

# Check for the method on the project object
print(hasattr(project.project, 'BeginUndoTask'))
print(hasattr(project.project.MainCacheAccessor, 'BeginUndoTask'))
```

**Expected answers:**
- [ ] `project.project.BeginUndoTask` exists (YES/NO)
- [ ] `project.MainCacheAccessor.BeginUndoTask` exists (YES/NO)
- [ ] Other location (where?): _____________

---

### Question 2: Does UndoStack.Mark Exist?

**What to test:**
```python
if hasattr(project.project, 'UndoStack'):
    undo_stack = project.project.UndoStack
    print(f"UndoStack exists: {undo_stack}")
    print(f"Has Mark: {hasattr(undo_stack, 'Mark')}")
    print(f"Has RollbackToMark: {hasattr(undo_stack, 'RollbackToMark')}")
```

**Expected answers:**
- [ ] `project.UndoStack` exists (YES/NO)
- [ ] `UndoStack.Mark()` exists (YES/NO)
- [ ] `UndoStack.RollbackToMark()` exists (YES/NO)

---

### Question 3: Can BeginUndoTask Work Inside BeginNonUndoableTask?

**What to test:**
```python
# Temporarily modify FLExProject.OpenProject to NOT call BeginNonUndoableTask
# for this test, then:

project.project.MainCacheAccessor.BeginNonUndoableTask()

try:
    # Try to start an undoable task inside non-undoable
    project.project.BeginUndoTask("test operation")
    project.LexEntry.Create("test_word", "stem")
    project.project.EndUndoTask()

    print("SUCCESS: BeginUndoTask works inside BeginNonUndoableTask")
    works_inside = True
except Exception as e:
    print(f"FAILED: {e}")
    works_inside = False
finally:
    project.project.MainCacheAccessor.EndNonUndoableTask()

return works_inside
```

**Expected answers:**
- [ ] BeginUndoTask works INSIDE NonUndoableTask envelope (YES/NO)
- [ ] If NO, is there an error message?______________________

---

### Question 4: What Are All the Undo/Redo Methods?

**What to test:**
```python
project_raw = project.project

# Inspect all undo-related methods
undo_methods = [
    m for m in dir(project_raw)
    if 'undo' in m.lower() or 'redo' in m.lower() or 'task' in m.lower()
]
print("Project-level undo/redo methods:")
for m in sorted(undo_methods):
    print(f"  - {m}")

mca_methods = [
    m for m in dir(project_raw.MainCacheAccessor)
    if 'undo' in m.lower() or 'redo' in m.lower() or 'mark' in m.lower() or 'task' in m.lower()
]
print("\nMainCacheAccessor undo/redo methods:")
for m in sorted(mca_methods):
    print(f"  - {m}")

if hasattr(project_raw, 'UndoStack'):
    us_methods = [
        m for m in dir(project_raw.UndoStack)
        if not m.startswith('_')
    ]
    print(f"\nUndoStack methods:")
    for m in sorted(us_methods):
        print(f"  - {m}")
```

**Expected answers:**
```
List all methods found:
Project level:
  - __________
  - __________

MainCacheAccessor level:
  - __________
  - __________

UndoStack level (if exists):
  - __________
  - __________
```

---

### Question 5: Does Undo/Redo Appear in FLEx Ctrl+Z?

**What to test:**
```python
# Prerequisites: FLEx must be OPEN with project sharing enabled

project = FLExProject()
project.OpenProject("SharedProject", writeEnabled=True, undoable=True)

# Note: This assumes question 3 answered YES - BeginUndoTask works

with project.UndoableOperation("TEST: Add entry 'xyztest'"):
    project.LexEntry.Create("xyztest", "stem")

project.SaveChanges()  # Ensure it's persisted

# Now look at FLEx window:
# - Is "TEST: Add entry 'xyztest'" visible in FLEx > Edit > Undo menu?
# - Can you Ctrl+Z and the entry disappears?
# - Can you Ctrl+Y and the entry reappears?
```

**Expected answers:**
- [ ] Operation appears in FLEx Ctrl+Z menu (YES/NO)
- [ ] Undo works from FLEx (YES/NO)
- [ ] Redo works from FLEx (YES/NO)

---

## Current State (Phase 1)

✅ Phase 1 **IMPLEMENTED**:
- `Transaction(label)` context manager for rollback-only
- `SaveChanges()` for checkpoint persistence
- Graceful fallback when rollback API is unavailable

❓ Phase 2 **PENDING RESEARCH**:
- BeginUndoTask / EndUndoTask existence and naming
- UndoStack.Mark / RollbackToMark availability
- Coexistence with BeginNonUndoableTask session model
- Undo/Redo method signatures and return types

---

## How to Contribute: Running the Research Tests

### Prerequisites

1. **FieldWorks 9+** installed and licensed
2. **Test project** available (create a new one or use existing)
3. **FlexLibs2** installed or in development mode
4. **Python** with pythonnet (Python.NET) available

### Step 1: Set Up Test Environment

```bash
cd flexlibs2
python -c "from flexlibs2 import FLExProject; print('FlexLibs2 OK')"
```

### Step 2: Create Research Script

Create a file `test_phase2_research.py`:

```python
#!/usr/bin/env python
#
# test_phase2_research.py
#
# Research script to verify Phase 2 LCM APIs
#

from flexlibs2 import FLExProject, FLExInitialize

FLExInitialize()
project = FLExProject()

try:
    project.OpenProject("TEST_UNDO")  # Use your test project name
    print("[TEST 1] BeginUndoTask detection...")
    # Copy Question 1 test code here

    print("\n[TEST 2] UndoStack.Mark detection...")
    # Copy Question 2 test code here

    print("\n[TEST 3] BeginUndoTask inside NonUndoableTask...")
    # Copy Question 3 test code here

    print("\n[TEST 4] All undo/redo methods...")
    # Copy Question 4 test code here

    print("\n[TEST 5] FLEx Ctrl+Z integration (MANUAL)...")
    print("Open FLEx and look for undo menu (see Question 5)")

finally:
    project.CloseProject()
```

### Step 3: Run and Collect Results

```bash
python test_phase2_research.py > research_results.txt 2>&1
```

### Step 4: Report Results

Create an issue or PR with:
1. Your FLEx version (Help > About)
2. Contents of `research_results.txt`
3. Answers to the manual test questions (Question 5)

---

## What Happens Next?

### If All Tests Pass (All YES)

✅ Phase 2 implementation can begin:
1. Create `flexlibs2/code/undoable_operation.py`
2. Add `undoable` parameter to `OpenProject()`
3. Add `UndoableOperation()`, `Undo()`, `Redo()` methods
4. Update documentation

### If Some Tests Fail (NO or Errors)

⚠️ Phase 2 on hold, but fallback available:
- Phase 1 (rollback-only) continues to work
- Users can manually call `SaveChanges()` for checkpoints
- Document workarounds in TRANSACTION_GUIDE.md

### If Tests Inconclusive (Different Results Across FW Versions)

❓ Version-specific implementation needed:
- Detect FLEx version at runtime
- Use different API paths for different versions
- Document version requirements in TRANSACTION_GUIDE.md

---

## Timeline

- **Phase 1**: DONE ✅ (as of 2025-03-16)
- **Phase 2**: Pending research ⏳
- **Phase 2 Research Target**: Within 2 weeks
- **Phase 2 Implementation**: 1-2 weeks after research completed

---

## Questions?

See `TRANSACTION_GUIDE.md` for Phase 1 usage details.

For Phase 2 research questions, file an issue with:
- Your FieldWorks version
- Python version
- Output from `test_phase2_research.py`

