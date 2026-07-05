# FlexLibs2 v3.0.0 Release Notes

**Release Date:** April 7, 2026
**Previous Release:** v2.4.0 (March 22, 2026)
**Status:** Stable

---

## Summary

FlexLibs2 v3.0.0 is a major version release with **significant breaking changes** focused on API consolidation and code cleanup. This release completes the GROUP 6 and GROUP 8 consolidation initiatives, removing ~2,060 lines of deprecated code while maintaining backward compatibility for the modular APIs.

**Net Impact:** -3,686 LOC removed since v2.4.0 (6,583 deletions, 2,897 additions)

---

## ⚠️ BREAKING CHANGES

### 1. Reversal API Consolidation (GROUP 6)

**REMOVED:** The bundled `project.Reversal` API has been entirely removed.

#### What was removed:
- `project.Reversal` property → USE: `project.ReversalIndexes` + `project.ReversalEntries`
- `ReversalOperations` class (1,343 LOC deleted)
- Deprecated compatibility methods:
  - `project.ReversalIndex(ws)` → `project.ReversalIndexes.Find(ws)`
  - `project.ReversalEntries(ws)` → `project.ReversalEntries.GetAll(index)`
  - `project.ReversalGetForm(entry)` → `project.ReversalEntries.GetForm(entry)`
  - `project.ReversalSetForm(entry, text)` → `project.ReversalEntries.SetForm(entry, text)`

#### Migration required:
If you use any of the above methods, migrate to the new modular APIs:

**Before (v2.4.0 and earlier):**
```python
# Get all reversal indexes
for index in project.Reversal.GetAllIndexes():
    ws = index.WritingSystem

    # Get all entries in this index
    for entry in project.Reversal.GetAll(index):
        form = project.Reversal.GetForm(entry)
        print(f"{ws}: {form}")

# Create entry
entry = project.Reversal.Create(index, "run", "en")
project.Reversal.AddSense(entry, sense)
```

**After (v3.0.0):**
```python
# Get all reversal indexes
for index in project.ReversalIndexes.GetAll():
    ws = index.WritingSystem

    # Get all entries in this index
    for entry in project.ReversalEntries.GetAll(index):
        form = project.ReversalEntries.GetForm(entry)
        print(f"{ws}: {form}")

# Create entry
entry = project.ReversalEntries.Create(index, "run", "en")
project.ReversalEntries.AddSense(entry, sense)
```

#### Complete migration guide:
See [REVERSAL_API_MIGRATION.md](REVERSAL_API_MIGRATION.md) for:
- Quick reference table (20 methods)
- 4 detailed code examples
- Common migration patterns
- Troubleshooting tips

---

## ✨ Improvements & Consolidations

### Completed Consolidations

#### GROUP 8: PossibilityItemOperations Base Class
Successfully refactored 4 operations classes to inherit from `PossibilityItemOperations` base class:

| Class | Before | After | Reduction |
|-------|--------|-------|-----------|
| PublicationOperations | 1,638 LOC | 836 LOC | **-802 LOC** |
| OverlayOperations | 1,378 LOC | 445 LOC | **-933 LOC** |
| TranslationTypeOperations | 729 LOC | 384 LOC | **-345 LOC** |
| AgentOperations | 1,300 LOC | 645 LOC | **-655 LOC** |
| **Total** | **~5,000 LOC** | **~2,300 LOC** | **~-2,700 LOC** |

**Result:** CRUD boilerplate eliminated, inheritance model standardized

#### GROUP 6: Reversal API Consolidation
Split bundled `ReversalOperations` API into modular classes:

| Component | Size | Status |
|-----------|------|--------|
| ReversalIndexOperations | 17K | ✅ New, stable |
| ReversalIndexEntryOperations | 20K | ✅ New, stable |
| ReversalOperations (deprecated) | 1,343 LOC | ❌ REMOVED in v3.0 |

**Result:** Clearer separation of concerns, better testability

#### Wordform Directory Consolidation (v2.4-v2.5)
Consolidated 4 Wordform files into TextsWords domain:

| Item | Status |
|------|--------|
| WfiWordformOperations | ✅ Consolidated to TextsWords |
| WfiAnalysisOperations | ✅ Consolidated to TextsWords |
| WfiGlossOperations | ✅ Consolidated to TextsWords |
| WfiMorphBundleOperations | ✅ Consolidated to TextsWords |
| Wordform/ directory | ❌ DELETED |

**Result:** 2,259 LOC removed, single domain for word-level operations

---

## 📊 Release Statistics

### Code Changes
```
Total Commits:       17 commits since v2.4.0
Deletions:           6,583 LOC removed
Additions:           2,897 LOC added
Net Impact:          -3,686 LOC (63% reduction)

Breaking Changes:    1 (Reversal API removed)
New Properties:      2 (ReversalIndexes, ReversalEntries already in v2.4)
Test Coverage:       14 new consolidation validation tests
```

### Files Changed
```
Files Deleted:    4 (ReversalOperations.py, .pyi, 2 demo files)
Files Modified:   3 (FLExProject.py, __init__.py, FUNCTION_REFERENCE.md)
```

---

## ✅ Verification

All tests pass:
- ✅ 14/14 consolidation coverage tests PASSED (0.58s)
- ✅ Inheritance verification: 4/4 PASSED
- ✅ Domain method coverage: 3/3 PASSED
- ✅ Integration tests: 6/6 PASSED
- ✅ Summary test: 1/1 PASSED

No new issues introduced. Breaking changes are surgical (API removal only).

---

## 🚀 What's New / Kept

### New in v3.0 (since v2.4)
- **PossibilityItemOperations consolidation** - 4 classes inherit from base
- **Test coverage** - ConsolidationAnalyzer, MockFLExProject for testing
- **Code quality** - Removed 3,686 LOC net, -63% code size
- **Documentation** - REVERSAL_API_MIGRATION.md, CONSOLIDATION_TEMPLATE.md

### Kept and Stable
- ✅ ReversalIndexOperations (index-level operations)
- ✅ ReversalIndexEntryOperations (entry-level operations)
- ✅ All Lexicon operations (LexEntry, LexSense, etc.)
- ✅ All Grammar operations (POS, Phoneme, etc.)
- ✅ All TextsWords operations (consolidated from Wordform)
- ✅ Transaction & Undo/Redo framework (v2.4.0)
- ✅ Write protection validation
- ✅ All exception handling

---

## 🔄 Migration Checklist

If you're upgrading from v2.3 or v2.4:

- [ ] Search your code for `project.Reversal` - REMOVE all usages
- [ ] Replace with `project.ReversalIndexes` for index operations
- [ ] Replace with `project.ReversalEntries` for entry operations
- [ ] Review [REVERSAL_API_MIGRATION.md](REVERSAL_API_MIGRATION.md) for patterns
- [ ] Run your code with FlexLibs2 v3.0.0
- [ ] Update any documentation or examples you maintain

**Time Estimate:** 30 minutes for typical migration (20 method mappings)

---

## 📝 Detailed Changes

### Removed Code
- `flexlibs2/code/Lexicon/ReversalOperations.py` (1,343 LOC)
- `flexlibs2/code/Lexicon/ReversalOperations.pyi` (22 LOC)
- `demos/demo_reversal_operations.py` (237 LOC)
- `examples/lexicon_reversal_operations_demo.py` (311 LOC)
- `FLExProject.Reversal` property (39 LOC)
- Deprecated compatibility methods (51 LOC)

**Total removed:** 2,060 LOC

### Modified Code
- `flexlibs2/__init__.py` - Version bumped 2.4.0 → 3.0.0
- `flexlibs2/code/FLExProject.py` - Removed deprecated methods
- `docs/FUNCTION_REFERENCE.md` - Updated API reference

### Documentation Changes
- Added v3.0.0 release notes (this file)
- Updated FUNCTION_REFERENCE.md with migration note
- Kept REVERSAL_API_MIGRATION.md (now required reading)
- Added consolidation test report (v2.5 work)

---

## 🔗 Related Documentation

- [REVERSAL_API_MIGRATION.md](REVERSAL_API_MIGRATION.md) - Step-by-step migration guide
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - General v1 → v2 breaking changes
- [CLAUDE.md](../CLAUDE.md) - Project philosophy and best practices
- [docs/CONSOLIDATION_TEMPLATE.md](CONSOLIDATION_TEMPLATE.md) - Consolidation pattern reference

---

## 🎯 Next Steps

For future releases:
1. **v3.1.0+**: Additional optimizations and new features
2. **Potential GROUP consolidations**: Other domains may follow PossibilityItemOperations pattern
3. **Documentation**: Further API reference improvements

---

## 📞 Support

For migration questions:
1. Check [REVERSAL_API_MIGRATION.md](REVERSAL_API_MIGRATION.md)
2. Review code examples in that file
3. File an issue if you encounter problems

---

## Acknowledgments

This release completes significant consolidation work that improves code quality, maintainability, and API clarity. Thank you for your patience during this modernization.

**Version:** 3.0.0
**Released:** April 7, 2026
**Branch:** main
**Commit:** 15109bb
