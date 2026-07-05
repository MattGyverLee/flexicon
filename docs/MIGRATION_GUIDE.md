# FlexLibs → FlexLibs2 Migration Guide

FlexLibs2 is a major version upgrade (2.0) with improvements to API consistency and user experience. This guide covers breaking changes and how to update your scripts.

## Breaking Change: Empty Multistring Field Handling

### What Changed

FlexLibs2 **automatically converts FLEx's empty placeholder ("***") to Python's empty string ("")** in all functions that return multistring field values (glosses, definitions, forms, etc.).

| Behavior | FlexLibs (v1.x) | FlexLibs2 (v2.0) |
|----------|-----------------|------------------|
| `LexiconGetSenseGloss(sense)` | Returns `"***"` | Returns `""` |
| `sense.Gloss.BestAnalysisAlternative.Text` | Returns `"***"` | Still returns `"***"` (raw C# result) |
| Requires `BestStr()` wrapping? | Sometimes | No (automatic) |

### Why This Changed

**Consistency Problem in FlexLibs:**
- Most methods use `or ""` fallback (don't explicitly handle "***")
- Some methods explicitly check for "***" (BestStr, custom fields)
- Users had to know which methods needed wrapping and which didn't

**Better UX in FlexLibs2:**
- All public functions automatically normalize empty strings
- Users write simpler, more Pythonic code
- No need to learn the "***" FLEx convention

### Migration: Check for "***"

If your script checks for the "***" placeholder, update it:

**Before (FlexLibs):**
```python
gloss = project.LexiconGetSenseGloss(sense)
if gloss == "***":
    print("Gloss is empty")
```

**After (FlexLibs2):**
```python
gloss = project.LexiconGetSenseGloss(sense)
if not gloss:  # or: if gloss == ""
    print("Gloss is empty")
```

### Migration: BestStr() Wrapping

If your script wrapped results with `BestStr()`, you can remove it:

**Before (FlexLibs):**
```python
# Sometimes needed because some methods return "***"
gloss = project.BestStr(sense.Gloss)
form = project.BestStr(entry.LexemeFormOA.Form)
definition = project.BestStr(sense.Definition)
```

**After (FlexLibs2):**
```python
# Not needed - these already return normalized strings
gloss = sense.Gloss.BestAnalysisAlternative.Text  # Still "***" if direct access
# Better: use the operation methods which do the normalization
# (This assumes we've created SenseOperations methods)
```

### Migration: Direct C# Field Access

If your script accesses C# objects directly (not through FlexLibs methods), you'll still get "***":

**Before (FlexLibs):**
```python
# Direct access - you see "***"
text = sense.Gloss.BestAnalysisAlternative.Text
if text == "***":
    print("Empty")
```

**After (FlexLibs2):**
```python
# Direct access still returns "***" (raw C#)
text = sense.Gloss.BestAnalysisAlternative.Text
if text == "***":
    print("Empty")  # Still need this check

# Better: use FlexLibs2 operations methods
# (These do automatic conversion)
gloss = SenseOperations.GetGloss(sense)  # Returns ""
```

---

## Summary of Changes

| Feature | FlexLibs | FlexLibs2 | Action |
|---------|----------|-----------|--------|
| Empty multistring handling | Inconsistent | Automatic (all functions) | Remove "***" checks, use `if not value:` instead |
| BestStr() utility | Available | Still available (but not needed) | Can remove from scripts |
| Direct C# field access | Returns "***" | Still returns "***" | If using direct access, keep "***" checks |
| Function return values | Mixed | Consistent "" | Update empty checks |

---

## Testing Your Migration

Quick checklist:
- [ ] Search your script for `== "***"` - change to `== ""` or `if not value:`
- [ ] Search for `BestStr()` calls - can usually remove them
- [ ] Test with entries/senses that have empty glosses/definitions
- [ ] Verify your conditional logic still works

---

## Questions?

See [CLAUDE.md](../CLAUDE.md) for more details on FLEx conventions and data handling.

---

## v2 to v3 Migration

FlexLibs2 v3.0.0 (April 7, 2026) introduced two breaking changes. If you are upgrading from
any v2.x release, check both sections below.

### 1. Removed: `project.Reversal` API

The bundled `project.Reversal` namespace was removed entirely. Replace each call with the
equivalent modular API:

| v2.x (removed) | v3.0 replacement |
|---|---|
| `project.Reversal.GetAllIndexes()` | `project.ReversalIndexes.GetAll()` |
| `project.Reversal.GetAll(index)` | `project.ReversalEntries.GetAll(index)` |
| `project.Reversal.GetForm(entry)` | `project.ReversalEntries.GetForm(entry)` |
| `project.Reversal.SetForm(entry, text)` | `project.ReversalEntries.SetForm(entry, text)` |
| `project.Reversal.Create(index, form, ws)` | `project.ReversalEntries.Create(index, form, ws)` |
| `project.Reversal.AddSense(entry, sense)` | `project.ReversalEntries.AddSense(entry, sense)` |
| `project.ReversalIndex(ws)` | `project.ReversalIndexes.Find(ws)` |

**Before (v2.x):**
```python
for index in project.Reversal.GetAllIndexes():
    ws = index.WritingSystem
    for entry in project.Reversal.GetAll(index):
        print(project.Reversal.GetForm(entry))
```

**After (v3.0):**
```python
for index in project.ReversalIndexes.GetAll():
    ws = index.WritingSystem
    for entry in project.ReversalEntries.GetAll(index):
        print(project.ReversalEntries.GetForm(entry))
```

See [REVERSAL_API_MIGRATION.md](REVERSAL_API_MIGRATION.md) for the complete 20-method table
and additional code examples.

### 2. Lists Consolidation (GROUP 8)

`AgentOperations`, `PublicationOperations`, `TranslationTypeOperations`, and `OverlayOperations`
now inherit from `PossibilityItemOperations`. For most callers **no code changes are needed** —
the same CRUD methods are available under the same names.

Known caveats:
- `AgentOperations` (#54) and `OverlayOperations` (#149) have partial parent-class fit problems;
  a small number of inherited methods may not function correctly in edge cases.

See [RELEASE_v3_0_0.md](internal/RELEASE_v3_0_0.md) for the full consolidation table and change details.

---

# v2.4 → v2.5 Migration

## Breaking Change: `flat=` → `recursive=` on hierarchical-list `GetAll`

### What Changed

Every hierarchical-list `GetAll()` accessor (POS, LexSense, SemanticDomain, Anthropology, Location, Publication, PossibilityLists, plus the inline `GetSubcategories` / `GetSubdomains` / `GetSubitems` helpers) standardized on a single parameter name. The old `flat=` is renamed to `recursive=` and the default is now `recursive=True` -- the intuitive "give me everything under this node" query is the one with no argument.

| Behavior | v2.4 | v2.5 |
|---|---|---|
| `POS.GetAll()` (no args) | Top-level only (~30) | All POSs including subcategories (~80) |
| `POS.GetAll(flat=True)` | Returns all | Raises `TypeError` |
| `POS.GetAll(recursive=False)` | -- | Top-level only |
| `LexEntry.GetAvailableMorphTypes(include_subcategories=True)` | Worked | Raises `TypeError` |
| `LexEntry.GetAvailableMorphTypes(recursive=True)` | -- | Works |
| `FLExProject.GetAllSemanticDomains(flat=True)` | Works | Raises `TypeError` |

### Why This Changed

The intuitive query ("give me everything under this category") was the harder one to spell when `flat=False` was the default for some accessors and `flat=True` for others. Standardizing on `recursive=True` as the default for collection queries lets the common case stay simple and the specialized case (`recursive=False`) stay explicit. See #100 and #101 for the full story.

### Migration: rename `flat=` to `recursive=`

**Before (v2.4):**
```python
poses = project.POS.GetAll(flat=True)
domains = project.SemanticDomains.GetAll(flat=True)
```

**After (v2.5):**
```python
poses = project.POS.GetAll()              # recursive by default
domains = project.SemanticDomains.GetAll()
# or, for top-level only:
top_poses = project.POS.GetAll(recursive=False)
```

### Migration: `include_subcategories=` -> `recursive=`

**Before:**
```python
mt = project.LexEntry.GetAvailableMorphTypes(include_subcategories=True)
```

**After:**
```python
mt = project.LexEntry.GetAvailableMorphTypes(recursive=True)
```

## Behavior Change: counting queries default to FLEx UI parity (direct-only)

### What Changed

Counting queries (`POSOperations.GetEntryCount`, `SemanticDomainOperations.GetSenseCount`) default to `recursive=False` -- they count only objects tagged with the requested category exactly, matching every count column FLEx itself surfaces (Categories tool, Lexicon Browse view, Tools > Statistics). The previous v2.4 default of `recursive=True` for `GetEntryCount` was reverted in #101 because users would see flexlibs2 reporting ~3x the counts FLEx shows and assume flexlibs2 was wrong.

The two distinct user questions:

- "How many entries match this tag?"             -> `GetEntryCount(noun)`            (direct, FLEx UI parity)
- "How many entries match this tag or descendants?" -> `GetEntryCount(noun, recursive=True)`

**No caller code change is required for the common path.** If you previously relied on the brief recursive=True default that shipped between d423e83 and the #101 revert, pass it explicitly.

### Migration

**Before (v2.4 / d423e83):**
```python
n = project.POS.GetEntryCount(noun)               # rolled up descendants
```

**After (v2.5):**
```python
n = project.POS.GetEntryCount(noun)               # direct-tagged only (FLEx UI parity)
n = project.POS.GetEntryCount(noun, recursive=True)  # roll up
n = project.SemanticDomains.GetSenseCount(dom)    # direct-tagged only
n = project.SemanticDomains.GetSenseCount(dom, recursive=True)  # roll up
```

### Migration: Detect-and-Fix Recipe

```bash
# Find all callers using the old flat= kwarg
rg --type py 'GetAll\(.*flat='
rg --type py 'GetAvailableMorphTypes\(.*include_subcategories='
```

Replace `flat=` with `recursive=` (same boolean value). Replace `include_subcategories=True` with `recursive=True`.

---
