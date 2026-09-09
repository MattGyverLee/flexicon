## Linguistic Safety Guide for FLEx Sync Framework

**Version**: 1.2.0 (Phase 2.5)
**Date**: 2025-11-27
**Status**: REQUIRED READING for all linguistic data operations

---

## ⚠️ CRITICAL SAFETY WARNINGS

### DO NOT USE for Production Linguistic Data Until You Read This

The sync framework v1.1.0 (Phase 2) was designed by software engineers without adequate linguistic consultation. **Version 1.2.0 (Phase 2.5) adds critical safety features** but still has limitations.

### What Can Go Wrong

**Data Loss Scenarios:**
1. **Orphaned Semantic Classifications** - Senses lose their semantic domain links
2. **Broken Grammar References** - POS/MSA references become null
3. **Lost Phonological Conditioning** - Allomorphs imported without their environments
4. **Destroyed Variant Relationships** - Morphological connections severed
5. **Missing Examples** - Owned objects not cascaded

**Each of these can represent YEARS of community consultant work.**

---

## Safe vs Unsafe Operations

### ✅ SAFE: Selective Import (NEW in v1.2.0)

```python
from flexicon.sync import SelectiveImport
from datetime import datetime

# This is the SAFE way for linguistic data
importer = SelectiveImport(source_project, target_project)

result = importer.import_new_objects(
    object_type="Allomorph",
    created_after=backup_timestamp,  # Only new objects
    validate_references=True,         # Check for orphans
    dry_run=True                     # Preview first!
)
```

**Why it's safe:**
- ✅ One-way operation (protects stable project)
- ✅ Only imports NEW objects (never overwrites)
- ✅ Validates references (prevents orphans)
- ✅ Dry-run preview required

### ❌ UNSAFE: Bidirectional Sync

```python
from flexicon.sync import SyncEngine

# DON'T DO THIS with production linguistic data!
sync = SyncEngine(source, target)
result = sync.sync(
    object_type="Allomorph",
    conflict_resolver="source_wins"  # ❌ DANGEROUS!
)
```

**Why it's dangerous:**
- ❌ Bidirectional (can corrupt both projects)
- ❌ No date filtering (syncs everything)
- ❌ Overwrites existing data
- ❌ No reference validation
- ❌ Can sync deletions

---

## Linguistic Workflow: Step by Step

### Scenario: Test Grammar Changes, Import New Allomorphs

**This is the use case the framework was originally designed for.**

#### Step 1: Backup Your Project

```python
# Before making ANY changes
backup_time = datetime.now()
print(f"Backup timestamp: {backup_time}")

# Make a complete copy (use FLEx or Mercurial)
# FlexTools: flextools.CopyProject("StableProject", "GrammarTest")
```

**Critical: Record the exact backup time!**

#### Step 2: Work in Test Project

```
- Open GrammarTest (NOT StableProject)
- Add your new phonological rules
- Create new allomorphs for those rules
- Test on your corpus
- Verify everything works
```

**DO NOT modify StableProject yet!**

#### Step 3: Preview Import (Dry Run)

```python
from flexicon.sync import SelectiveImport

# Open projects
# test_proj = flextools.OpenProject("GrammarTest")
# stable_proj = flextools.OpenProject("StableProject", writeEnabled=True)

importer = SelectiveImport(
    source_project=test_proj,
    target_project=stable_proj
)

# DRY RUN - just preview
result = importer.import_new_objects(
    object_type="Allomorph",
    created_after=backup_time,      # Only objects created after backup
    validate_references=True,        # Check for missing POS, morph types, etc.
    dry_run=True                    # NO CHANGES YET
)

# Review what WOULD be imported
print(result.summary())
print(f"\nWould import: {result.num_skipped} new allomorphs")

# Check for validation errors
if result.num_errors > 0:
    print("\n❌ VALIDATION ERRORS:")
    for error in result.errors:
        print(f"  - {error.error_message}")
    print("\n⚠️  Cannot proceed - fix errors first!")
else:
    print("\n✅ Validation passed - safe to import")
```

#### Step 4: Review and Confirm

**BEFORE running actual import, verify:**

- [ ] Backup timestamp is correct
- [ ] Number of objects looks reasonable
- [ ] No validation errors
- [ ] You have a recent backup
- [ ] Test project changes are finalized

#### Step 5: Execute Import

```python
# Only if dry run looked good!
if input("Proceed with import? (yes/no): ") == "yes":
    result = importer.import_new_objects(
        object_type="Allomorph",
        created_after=backup_time,
        validate_references=True,
        dry_run=False              # ACTUALLY IMPORT
    )

    print(f"\n✅ Imported {result.num_created} new allomorphs")

    if result.num_errors > 0:
        print(f"⚠️  {result.num_errors} errors occurred")
        print("Check logs for details")
```

#### Step 6: Verify Results

```
- Open StableProject in FLEx
- Check that new allomorphs appear
- Run parser to verify they work correctly
- Check cross-references are intact
- Run FLEx consistency check
```

**If anything looks wrong: Restore from backup immediately!**

---

## Reference Validation Explained

### What Gets Validated

The validation framework checks for:

1. **POS/MSA References**
   - Ensures referenced Part of Speech exists in target
   - Prevents null grammar links

2. **Semantic Domains**
   - Ensures referenced domains exist in target
   - Prevents orphaned semantic classifications

3. **Morph Types**
   - Ensures referenced morph types (stem, root, affix) exist
   - Prevents type mismatches

4. **Parent Objects**
   - Ensures owner entry/sense exists
   - Prevents orphaned objects

5. **Data Quality**
   - Warns about empty glosses
   - Warns about missing forms
   - Informational only

### Validation Severity Levels

**CRITICAL** (❌ Blocks operation):
- Missing POS/MSA reference
- Missing semantic domain
- Missing morph type
- Missing parent object

**WARNING** (⚠️ User should review):
- Object has owned children that won't be copied
- Data quality issues (empty fields)

**INFO** (ℹ️ Informational):
- Entry has no senses
- Sense has no examples

### Handling Validation Failures

```python
result = importer.import_new_objects(
    object_type="LexSense",
    created_after=backup_time,
    validate_references=True,
    dry_run=True
)

if result.num_errors > 0:
    print("❌ VALIDATION FAILURES:")
    for error in result.errors:
        print(f"  {error.error_message}")

    print("\nOPTIONS:")
    print("1. Import missing references first (POS, semantic domains)")
    print("2. Manually map references to target equivalents")
    print("3. Accept data loss and skip validation")
    print("   (NOT RECOMMENDED)")
```

---

## What's Still Missing (Limitations)

### Current Limitations (v1.2.0)

1. **No Hierarchical Cascade**
   - Senses don't import with their examples
   - Entries don't import with all senses
   - Allomorphs don't import with phonological environments
   - **Workaround**: Import each level separately

2. **No Cross-Reference Copying**
   - Variant links not preserved
   - Reversal entries not copied
   - Etymology links lost
   - **Workaround**: Manually reconstruct references

3. **No Owned Object Cascade**
   - Examples must be imported separately
   - Phonological environments not included
   - **Workaround**: Validation warns you about these

4. **Limited Filtering**
   - Can filter by date only
   - No morphological type filtering
   - No semantic domain filtering
   - **Workaround**: Use `import_by_filter()` with custom function

### Planned for Phase 3 (Dependency Safety)

- Hierarchical cascade operations
- Cross-reference preservation
- Owned object inclusion
- Subsystem-aware filtering
- Paradigm completeness checking

---

## Common Scenarios

### Scenario 1: Import New Lexical Entries

```python
importer = SelectiveImport(source, target)

result = importer.import_new_objects(
    object_type="LexEntry",
    created_after=field_trip_start_date,
    validate_references=True,
    dry_run=False
)
```

**⚠️  WARNING**: Entries will be imported WITHOUT:
- Their senses
- Their allomorphs
- Their examples

**You must import these separately** (Phase 3 will fix this).

### Scenario 2: Import Only Verified Data

```python
def is_verified(obj):
    """Check if linguist marked as verified."""
    return hasattr(obj, 'Status') and obj.Status == 'Verified'

result = importer.import_by_filter(
    object_type="Allomorph",
    filter_fn=is_verified,
    validate_references=True
)
```

### Scenario 3: Import Specific Morph Type

```python
def is_stem(obj):
    """Filter for stems only (not affixes)."""
    if hasattr(obj, 'MorphTypeRA'):
        morph_type = obj.MorphTypeRA
        if morph_type and hasattr(morph_type, 'Name'):
            name = morph_type.Name.AnalysisDefaultWritingSystem
            return 'stem' in name.lower() or 'root' in name.lower()
    return False

result = importer.import_by_filter(
    object_type="Allomorph",
    filter_fn=is_stem,
    validate_references=True
)
```

### Scenario 4: Import from Multiple Sources

```python
# Import from Consultant A's project
importer_a = SelectiveImport(consultant_a_project, main_project)
result_a = importer_a.import_new_objects(
    object_type="LexEntry",
    created_after=consultant_a_start_date
)

# Import from Consultant B's project
importer_b = SelectiveImport(consultant_b_project, main_project)
result_b = importer_b.import_new_objects(
    object_type="LexEntry",
    created_after=consultant_b_start_date
)

print(f"Total imported: {result_a.num_created + result_b.num_created} entries")
```

---

## Troubleshooting

### Error: "Referenced POS/MSA does not exist"

**Problem**: Source sense references a Part of Speech that doesn't exist in target.

**Solution**:
1. Import POS list from source to target first
2. Or manually create matching POS in target
3. Or map source POS to existing target POS (manual)

### Error: "Semantic domain not found in target"

**Problem**: Source uses different semantic domain list than target.

**Solution**:
1. Use same semantic domain list in both projects
2. Or map source domains to target equivalents
3. Or accept that semantic classification will be lost

### Error: "Parent entry does not exist"

**Problem**: Trying to import allomorph whose parent entry isn't in target.

**Solution**:
1. Import parent entry first
2. Then import allomorphs

### Warning: "Object has N example(s) that will NOT be copied"

**Problem**: Owned objects aren't cascaded yet (Phase 3 feature).

**Solution**:
1. Accept warning (examples won't be imported)
2. Or import examples separately after senses
3. Or wait for Phase 3 cascade support

---

## Best Practices

### 1. Always Backup First

```python
# BEFORE any import operation
backup_path = flextools.BackupProject(project_name)
print(f"Backup saved to: {backup_path}")
```

### 2. Always Dry Run First

```python
# NEVER skip dry run on production data
result = importer.import_new_objects(
    object_type="Allomorph",
    created_after=backup_time,
    dry_run=True  # ALWAYS TRUE FIRST
)

# Review results...

# Only then do real import
if looks_good:
    result = importer.import_new_objects(..., dry_run=False)
```

### 3. Always Validate References

```python
# NEVER disable validation on production data
result = importer.import_new_objects(
    object_type="LexSense",
    validate_references=True  # ALWAYS TRUE
)
```

### 4. Work on Copies, Not Originals

```
✅ DO: StableProject → TestCopy → make changes → import to StableProject
❌ DON'T: Make changes directly in StableProject
```

### 5. Test on Non-Critical Data First

```
✅ DO: Test on practice project or old abandoned project
❌ DON'T: Test on your 10-year endangered language documentation
```

### 6. Version Control Everything

```
✅ DO: Use Mercurial/Git for project versioning
❌ DON'T: Rely only on FLEx backups
```

### 7. Document Your Imports

```python
# Keep import log
import_log = f"""
Import Log
Date: {datetime.now()}
Source: {source_name}
Target: {target_name}
Object Type: {object_type}
Backup Time: {backup_time}
Objects Imported: {result.num_created}
Errors: {result.num_errors}
"""

with open("import_log.txt", "a") as f:
    f.write(import_log)
```

---

## When to Use Which Tool

### Use SelectiveImport when:
- ✅ Importing from backup/test project to stable
- ✅ Importing consultant corrections
- ✅ Merging field work data
- ✅ Importing specific object types
- ✅ Working with production linguistic data

### Use SyncEngine when:
- ⚠️  Syncing non-linguistic data (maybe)
- ⚠️  Both projects are expendable
- ⚠️  You fully understand the risks
- ❌ NEVER with production linguistic data

### Wait for Phase 3 when:
- Importing entries with all senses/examples
- Copying cross-references (variants, reversals)
- Merging complex hierarchical data
- Syncing grammatical subsystems

---

## Getting Help

### If You Encounter Issues

1. **Check validation output** - It tells you what's wrong
2. **Review this guide** - Common scenarios covered
3. **Try dry run** - See what would happen
4. **Check FLEx documentation** - Understand object relationships
5. **Ask on FlexTools forum** - Community support

### Reporting Bugs

Include:
- FLEx version
- flexlibs version (print `flexicon.sync.__version__`)
- Object type being imported
- Validation output
- Error messages
- What you expected vs what happened

---

## Summary

### DO:
- ✅ Use `SelectiveImport` for linguistic data
- ✅ Always run dry_run=True first
- ✅ Always validate_references=True
- ✅ Always backup before importing
- ✅ Filter by date (created_after/modified_after)
- ✅ Review validation output
- ✅ Test on copies first

### DON'T:
- ❌ Use `SyncEngine` on production data
- ❌ Skip validation
- ❌ Skip dry run
- ❌ Import without backup
- ❌ Ignore validation warnings
- ❌ Disable safety checks

### REMEMBER:
**Years of community consultant work can be lost in seconds. When in doubt, don't import.**

---

**Document Version**: 1.0
**Framework Version**: 1.2.0 (Phase 2.5)
**Last Updated**: 2025-11-27
**Status**: Required Reading for All Users
