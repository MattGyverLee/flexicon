# Reversal API Migration Guide

This guide helps you migrate from the deprecated `ReversalOperations` bundled API to the new decomposed `ReversalIndexOperations` and `ReversalIndexEntryOperations` APIs.

## Why Change?

The new API splits index-level and entry-level operations into separate classes, providing:
- Clearer separation of concerns
- Better testability
- Explicit operations instead of bundled methods
- Better alignment with Flexicon architecture
- Improved discoverability of available operations

## Migration Timeline

- **flexicon v2.5+**: Deprecation warnings active, migration guide available
- **flexicon v3.0**: Bundled API methods removed (requires user migration)

## Quick Reference: Migration Table

| Old API (Deprecated) | New API | Notes |
|---|---|---|
| `project.Reversal.GetAllIndexes()` | `project.ReversalIndexes.GetAll()` | Get all reversal indexes |
| `project.Reversal.GetIndex(ws)` | `project.ReversalIndexes.Find(ws)` | Get index by writing system |
| `project.Reversal.FindIndex(ws)` | `project.ReversalIndexes.FindByWritingSystem(ws)` | Alias for GetIndex (use Find) |
| `project.Reversal.Create(idx, form)` | `project.ReversalEntries.Create(idx, form)` | Create entry under index |
| `project.Reversal.Delete(entry)` | `project.ReversalEntries.Delete(entry)` | Delete entry |
| `project.Reversal.Find(idx, form)` | `project.ReversalEntries.Find(idx, form)` | Find entry by form |
| `project.Reversal.GetAll(idx)` | `project.ReversalEntries.GetAll(idx)` | Get all entries in index |
| `project.Reversal.Exists(idx, form)` | `project.ReversalEntries.Exists(idx, form)` | Check if entry exists |
| `project.Reversal.GetForm(entry)` | `project.ReversalEntries.GetForm(entry)` | Get entry form text |
| `project.Reversal.SetForm(entry, text)` | `project.ReversalEntries.SetForm(entry, text)` | Set entry form text |
| `project.Reversal.GetSenses(entry)` | `project.ReversalEntries.GetSenses(entry)` | Get linked senses |
| `project.Reversal.AddSense(entry, sense)` | `project.ReversalEntries.AddSense(entry, sense)` | Link sense to entry |
| `project.Reversal.RemoveSense(entry, sense)` | `project.ReversalEntries.RemoveSense(entry, sense)` | Unlink sense from entry |
| `project.Reversal.GetSubentries(entry)` | `project.ReversalEntries.GetSubentries(entry)` | Get subentries |
| `project.Reversal.CreateSubentry(parent, form)` | `project.ReversalEntries.CreateSubentry(parent, form)` | Create subentry |
| `project.Reversal.GetParentEntry(entry)` | `project.ReversalEntries.GetParentEntry(entry)` | Get parent entry |
| `project.Reversal.GetPartsOfSpeech(entry)` | `project.ReversalEntries.GetPartsOfSpeech(entry)` | Get parts of speech |
| `project.Reversal.Duplicate(entry)` | `project.ReversalEntries.Duplicate(entry)` | Duplicate entry |
| `project.Reversal.CompareTo(e1, e2)` | `project.ReversalEntries.CompareTo(e1, e2)` | Compare entries |
| `project.Reversal.GetSyncableProperties(entry)` | `project.ReversalEntries.GetSyncableProperties(entry)` | Get syncable properties |

## Code Examples

### Example 1: Iterate All Reversal Indexes and Entries

**Before (Deprecated API):**
```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

try:
    # Get all reversal indexes
    all_indexes = project.Reversal.GetAllIndexes()
    for index in all_indexes:
        ws = index.WritingSystem

        # Get all entries in this index
        entries = project.Reversal.GetAll(index)
        for entry in entries:
            form = project.Reversal.GetForm(entry)
            print(f"{ws}: {form}")
finally:
    project.CloseProject()
```

**After (New API):**
```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

try:
    # Get all reversal indexes
    all_indexes = project.ReversalIndexes.GetAll()
    for index in all_indexes:
        ws = index.WritingSystem

        # Get all entries in this index
        entries = project.ReversalEntries.GetAll(index)
        for entry in entries:
            form = project.ReversalEntries.GetForm(entry)
            print(f"{ws}: {form}")
finally:
    project.CloseProject()
```

### Example 2: Create Entry and Link to Sense

**Before (Deprecated API):**
```python
# Get English reversal index
en_index = project.Reversal.GetIndex("en")
if en_index:
    # Create entry
    entry = project.Reversal.Create(en_index, "running")

    # Get a sense and link it
    lex_entry = project.LexEntry.Find("run")
    if lex_entry:
        senses = project.LexEntry.GetSenses(lex_entry)
        if senses:
            project.Reversal.AddSense(entry, senses[0])
```

**After (New API):**
```python
# Get English reversal index
en_index = project.ReversalIndexes.Find("en")
if en_index:
    # Create entry
    entry = project.ReversalEntries.Create(en_index, "running")

    # Get a sense and link it
    lex_entry = project.LexEntry.Find("run")
    if lex_entry:
        senses = project.LexEntry.GetSenses(lex_entry)
        if senses:
            project.ReversalEntries.AddSense(entry, senses[0])
```

### Example 3: Find and Update Entry

**Before (Deprecated API):**
```python
en_index = project.Reversal.GetIndex("en")
if en_index:
    # Check if entry exists
    if project.Reversal.Exists(en_index, "walking"):
        entry = project.Reversal.Find(en_index, "walking")

        # Update the form
        project.Reversal.SetForm(entry, "walk_modern")

        # Get linked senses
        senses = project.Reversal.GetSenses(entry)
        print(f"Found {len(senses)} linked senses")
```

**After (New API):**
```python
en_index = project.ReversalIndexes.Find("en")
if en_index:
    # Check if entry exists
    if project.ReversalEntries.Exists(en_index, "walking"):
        entry = project.ReversalEntries.Find(en_index, "walking")

        # Update the form
        project.ReversalEntries.SetForm(entry, "walk_modern")

        # Get linked senses
        senses = project.ReversalEntries.GetSenses(entry)
        print(f"Found {len(senses)} linked senses")
```

### Example 4: Work with Subentries

**Before (Deprecated API):**
```python
parent_entry = project.Reversal.Find(en_index, "run")
if parent_entry:
    # Get all subentries
    subentries = project.Reversal.GetSubentries(parent_entry)

    # Create a subentry
    sub = project.Reversal.CreateSubentry(parent_entry, "run_fast")
```

**After (New API):**
```python
parent_entry = project.ReversalEntries.Find(en_index, "run")
if parent_entry:
    # Get all subentries
    subentries = project.ReversalEntries.GetSubentries(parent_entry)

    # Create a subentry
    sub = project.ReversalEntries.CreateSubentry(parent_entry, "run_fast")
```

## Deprecation Warnings

When you call deprecated methods, you will see warnings like:

```
DeprecationWarning: ReversalOperations.GetAllIndexes() is deprecated.
Use project.ReversalIndexes.GetAll() instead.
```

These warnings:
- Are enabled by default
- Will not cause your code to fail
- Can be suppressed in test suites with: `warnings.filterwarnings("ignore", category=DeprecationWarning)`

## Migration Checklist

- [ ] Replace all `project.Reversal.GetAllIndexes()` with `project.ReversalIndexes.GetAll()`
- [ ] Replace all `project.Reversal.GetIndex(ws)` with `project.ReversalIndexes.Find(ws)`
- [ ] Replace all `project.Reversal.FindIndex(ws)` with `project.ReversalIndexes.FindByWritingSystem(ws)` or `project.ReversalIndexes.Find(ws)`
- [ ] Replace all `project.Reversal.GetAll(idx)` with `project.ReversalEntries.GetAll(idx)`
- [ ] Replace all `project.Reversal.Create(idx, form)` with `project.ReversalEntries.Create(idx, form)`
- [ ] Replace all `project.Reversal.Delete(entry)` with `project.ReversalEntries.Delete(entry)`
- [ ] Replace all `project.Reversal.Find(idx, form)` with `project.ReversalEntries.Find(idx, form)`
- [ ] Replace all `project.Reversal.Exists(idx, form)` with `project.ReversalEntries.Exists(idx, form)`
- [ ] Replace all `project.Reversal.GetForm(entry)` with `project.ReversalEntries.GetForm(entry)`
- [ ] Replace all `project.Reversal.SetForm(entry, text)` with `project.ReversalEntries.SetForm(entry, text)`
- [ ] Replace all `project.Reversal.GetSenses(entry)` with `project.ReversalEntries.GetSenses(entry)`
- [ ] Replace all `project.Reversal.AddSense(entry, sense)` with `project.ReversalEntries.AddSense(entry, sense)`
- [ ] Replace all `project.Reversal.RemoveSense(entry, sense)` with `project.ReversalEntries.RemoveSense(entry, sense)`
- [ ] Replace all `project.Reversal.GetSubentries(entry)` with `project.ReversalEntries.GetSubentries(entry)`
- [ ] Replace all `project.Reversal.CreateSubentry(parent, form)` with `project.ReversalEntries.CreateSubentry(parent, form)`
- [ ] Replace all `project.Reversal.GetParentEntry(entry)` with `project.ReversalEntries.GetParentEntry(entry)`
- [ ] Replace all `project.Reversal.GetPartsOfSpeech(entry)` with `project.ReversalEntries.GetPartsOfSpeech(entry)`
- [ ] Replace all `project.Reversal.Duplicate(entry)` with `project.ReversalEntries.Duplicate(entry)`
- [ ] Replace all `project.Reversal.CompareTo(e1, e2)` with `project.ReversalEntries.CompareTo(e1, e2)`
- [ ] Replace all `project.Reversal.GetSyncableProperties(entry)` with `project.ReversalEntries.GetSyncableProperties(entry)`

## API Differences

### Method Name Changes
- `GetIndex(ws)` becomes `Find(ws)` - consistent with other operations classes
- `FindIndex(ws)` becomes `FindByWritingSystem(ws)` - more explicit name

### Organization
The new API splits into:
- **ReversalIndexOperations**: Index-level operations
  - GetAll() - list all indexes
  - Find(ws) - get index by writing system
  - FindByWritingSystem(ws) - alias for Find

- **ReversalIndexEntryOperations**: Entry-level operations
  - GetAll(index) - list entries in an index
  - Create(index, form) - create entry
  - Find(index, form) - find entry by form
  - And all other entry operations...

## Common Pitfalls

### Pitfall 1: Forgetting to Migrate GetIndex to Find
```python
# WRONG - will fail in v3.0
en_index = project.Reversal.GetIndex("en")

# RIGHT
en_index = project.ReversalIndexes.Find("en")
```

### Pitfall 2: Using Old Method Names
```python
# WRONG
entries = project.Reversal.GetAll(index)

# RIGHT
entries = project.ReversalEntries.GetAll(index)
```

### Pitfall 3: Forgetting to Update FindIndex
```python
# WRONG - will fail in v3.0
index = project.Reversal.FindIndex("en")

# RIGHT - use Find instead
index = project.ReversalIndexes.Find("en")

# OR FindByWritingSystem if explicitly desired
index = project.ReversalIndexes.FindByWritingSystem("en")
```

## Support

For questions or migration issues, open an issue on GitHub with `[REVERSAL-MIGRATION]` tag.

See also:
- [Flexicon API Documentation](../README.md)
- [ReversalIndexOperations API Reference](../docs/API_REFERENCE.md#reversalindexoperations)
- [ReversalIndexEntryOperations API Reference](../docs/API_REFERENCE.md#reversalindexentryoperations)
