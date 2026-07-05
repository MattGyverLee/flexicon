# Transaction Guide: Safe Rollback Operations in FlexLibs2

## Overview

FlexLibs2 Phase 1 introduces safe transaction rollback via context managers. If an error occurs during a series of database operations, all changes can be automatically rolled back to the state before the transaction started.

This guide covers **Phase 1 (rollback-only)** behavior. Phase 2 (full undo stack integration with FLEx Ctrl+Z) is pending research and will be documented separately.

---

## Quick Start

### Basic Transaction

```python
from flexlibs2 import FLExProject

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

try:
    with project.Transaction("import batch"):
        project.LexEntry.Create("run", "stem")
        project.LexEntry.Create("walk", "stem")
        project.LexEntry.Create("jump", "stem")
    # If all three create calls succeed, changes are kept
except Exception as e:
    # If any call raises, rollback is attempted
    print(f"Import failed: {e}")
finally:
    project.CloseProject()
```

### Save Immediately After Success

For large imports or when you want to ensure data is persisted before continuing:

```python
with project.Transaction("import batch 1"):
    for word in batch1:
        project.LexEntry.Create(word["form"], "stem")

project.SaveChanges()  # Persist to disk immediately
print("Batch 1 saved successfully")

with project.Transaction("import batch 2"):
    for word in batch2:
        project.LexEntry.Create(word["form"], "stem")

project.SaveChanges()  # Persist batch 2
```

---

## How It Works

### 1. Marking a Checkpoint

When you enter a `with project.Transaction(...)` block, FlexLibs2 attempts to mark a rollback point in the LCM undo stack:

```python
with project.Transaction("operation"):  # <-- Mark set here
    # ... do operations ...
    # If exception: rollback to mark
    # If success: keep changes
```

### 2. On Success (No Exception)

- Changes made inside the block are **kept**
- Changes are **not persisted to disk** until `SaveChanges()` or `CloseProject()` is called
- The mark is discarded

### 3. On Failure (Exception Raised)

- Rollback is attempted using the mark
- The original exception is **re-raised** (you still see the error)
- All changes from the transaction block are **reverted**
- Other transactions that completed successfully are unaffected

### 4. Special Case: Read-Only Project

- If the project was opened with `writeEnabled=False`, transactions silently skip marking
- Write operations will fail at the individual operation level with `FP_ReadOnlyError`

---

## Exception Handling

### Catching Transaction Errors

```python
from flexlibs2 import FLExProject, FP_TransactionError

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

try:
    with project.Transaction("import entries"):
        for entry_data in data:
            entry = project.LexEntry.Create(entry_data["word"], "stem")
            # Assuming this might fail for some entries:
            project.Senses.Create(entry, entry_data["gloss"], "en")
except FP_TransactionError as e:
    # FP_TransactionError: raised if Transaction setup fails
    print(f"Transaction system error: {e}")
except Exception as e:
    # Original exception from inside the block
    print(f"Operation failed and was rolled back: {e}")
finally:
    project.CloseProject()
```

### Rollback Failure

In rare cases, the rollback operation itself might fail:

```
WARNING: Transaction 'import': ROLLBACK FAILED: [error details]
Project may be in inconsistent state. Consider closing without saving.
```

If you see this warning:
1. **Do NOT** call `SaveChanges()` or proceed with more operations
2. **Close** the project WITHOUT saving:
   ```python
   # In your except block:
   del project  # Closes without saving
   ```
3. **Reopen** the project and manually check/fix the data

---

## Nesting Transactions

Nested transactions are **allowed** but have documented behavior:

```python
with project.Transaction("outer"):
    project.LexEntry.Create("word1", "stem")

    with project.Transaction("inner"):
        project.LexEntry.Create("word2", "stem")
        # If this fails...
    # ...rollback happens to outer's mark, not just inner's
```

**Key point:** The inner transaction shares the outer transaction's rollback mark. If the inner transaction fails, both the inner and outer operations revert.

**Recommendation:** Avoid nesting transactions in your code. If you need nested structure, use separate `with` blocks at the same level instead.

---

## SaveChanges() Method

### Purpose

Save pending changes to disk **without closing the project**. Useful for:
- Checkpoints during long import operations
- Ensuring data is persisted before next step
- Reducing data loss risk if project crashes

### Usage

```python
with project.Transaction("batch 1"):
    for item in items[0:100]:
        project.LexEntry.Create(item["word"], "stem")

project.SaveChanges()  # Flush to disk

with project.Transaction("batch 2"):
    for item in items[100:200]:
        project.LexEntry.Create(item["word"], "stem")

project.SaveChanges()  # Flush again
```

### Notes

- **No side effects on transactions**: calling `SaveChanges()` does NOT affect the undo stack or active transactions
- **Read-only projects**: raises `FP_ReadOnlyError` if project is not write-enabled
- **Session remains open**: the project stays open and usable after `SaveChanges()`

---

## When to Use Transactions

### ✅ Good Use Cases

- **Batch imports**: wrap multiple Create calls in a single transaction
  ```python
  with project.Transaction("import user data"):
      for row in csv_file:
          entry = project.LexEntry.Create(row["word"], "stem")
          project.Senses.Create(entry, row["definition"], "en")
  ```

- **Multi-step updates**: ensure all related changes succeed together
  ```python
  with project.Transaction("update entry and senses"):
      entry = project.LexEntry.Find("run")
      project.LexEntry.UpdateName(entry, "ran")
      # Also update related senses
      for sense in entry.senses:
          project.Senses.UpdateGloss(sense, new_gloss)
  ```

- **Conditional operations**: undo if validation fails
  ```python
  with project.Transaction("add entries if valid"):
      for entry_data in data:
          if not validate(entry_data):
              raise ValueError(f"Invalid: {entry_data}")
          project.LexEntry.Create(entry_data["word"], "stem")
  ```

### ❌ Avoid

- **Single operations**: no need for a transaction wrapper
  ```python
  # Don't do this:
  with project.Transaction("create entry"):
      project.LexEntry.Create("word", "stem")

  # Just do this:
  project.LexEntry.Create("word", "stem")
  ```

- **Very large batches**: consider chunking into smaller transactions
  ```python
  # Instead of one giant transaction with 100,000 items:
  for chunk in chunks(data, size=1000):
      with project.Transaction(f"import {chunk[0]} to {chunk[-1]}"):
          for item in chunk:
              project.LexEntry.Create(item["word"], "stem")
      project.SaveChanges()
  ```

---

## Phase 2: Full Undo Stack (Coming Soon)

Phase 2 will add:

- `project.UndoableOperation(label)` - context manager that adds to FLEx's Ctrl+Z menu
- `project.Undo()` / `project.Redo()` - methods to call FLEx undo/redo
- `undoable=True` parameter on `OpenProject()` to enable full undo stack support

Phase 2 requires research to verify the LCM APIs (BeginUndoTask, EndUndoTask, etc.) work correctly. See `docs/internal/RESEARCH_NEEDED.md` for details.

Until Phase 2:
- Transactions do NOT appear in FLEx's undo menu
- Manual undo in FLEx will NOT affect flexlibs2 operations that happened within a `BeginNonUndoableTask()` session
- FLEx Ctrl+Z is unavailable while using flexlibs2 (by design, to prevent user confusion)

---

## Troubleshooting

### "Transaction: no LCM rollback API found"

**What it means:** FlexLibs2 could not locate the LCM APIs needed for rollback.

**Why it happens:** The LCM method names (Mark, RollbackToMark) may be named differently or unavailable in your FieldWorks version.

**What happens:** Transactions still execute, but **rollback on failure is NOT available**. If an error occurs, changes are NOT automatically reverted.

**Fix:**
1. See `docs/internal/RESEARCH_NEEDED.md` for the list of APIs being researched
2. Report this issue with your FW version to the FlexLibs2 team

### Project appears inconsistent after rollback failure

**What to do:**
1. Do NOT call `SaveChanges()` or continue operations
2. Close the project WITHOUT saving:
   ```python
   import sys
   del project  # Closes without persisting
   sys.exit(1)  # Exit to prevent accidental save
   ```
3. Reopen the project in FLEx to check/repair data

### Transactions work, but changes aren't visible in FLEx

This is **expected**. FlexLibs2 runs in `BeginNonUndoableTask()` mode, which means:
- Changes are **not added** to FLEx's undo stack
- Changes are **persisted to the database** but not shown in FLEx's UI
- You must **close the project** in FlexLibs2 and **reopen it in FLEx** to see the changes

---

## API Reference

### FLExProject.Transaction(label="transaction")

**Parameters:**
- `label` (str): Description of the transaction, shown in logs. Default: `"transaction"`

**Returns:**
- Context manager that supports `with` statements

**Raises:**
- Nothing on entry (raises are caught in `__exit__`)

**Example:**
```python
with project.Transaction("import batch") as txn:
    # Operations here
```

### FLExProject.SaveChanges()

**Parameters:** None

**Returns:** None

**Raises:**
- `FP_ReadOnlyError` - if project is not write-enabled

**Example:**
```python
project.SaveChanges()  # Persist pending changes
```

---

## See Also

- `docs/internal/RESEARCH_NEEDED.md` - Details on Phase 2 research and API verification
- `flexlibs2.code.transaction._FLExTransaction` - Internal context manager class
- `FLExProject.OpenProject()` - How to open projects with write access
- `FP_ReadOnlyError`, `FP_TransactionError` - Exceptions

