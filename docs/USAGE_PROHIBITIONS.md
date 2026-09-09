# Morphosyntactic Prohibitions Usage Guide

**Version:** v2.3+
**API:** flexicon.code.Grammar
**Classes:** AdhocProhibition, ProhibitionCollection
**Base Class:** LCMObjectWrapper, SmartCollection

---

## Overview

Ad hoc morphosyntactic prohibitions define restrictions on which morphemes can combine with each other in a language. Flexicon v2.3 introduces a unified wrapper interface for working with ad hoc prohibitions, handling three concrete types transparently.

### What Are Prohibitions?

Prohibitions in FLEx restrict morpheme co-occurrence. They answer questions like:
- "Which morphemes can never follow this morpheme?"
- "Which grammatical features are incompatible?"
- "Which allomorph variants cannot combine with each other?"

---

## The Problem: Type Complexity

FLEx stores ad hoc prohibitions with three different concrete types:

```python
# Before v2.3 - Raw FLEx API
for prohib in project.MorphRules.GetAllAdhocCoProhibitions():
    class_name = prohib.ClassName  # "MoAdhocProhibGr", "MoAdhocProhibMorph", etc.

    if class_name == "MoAdhocProhibGr":
        # Access grammatical prohibition properties
        feature = prohib.FeatureRA
    elif class_name == "MoAdhocProhibMorph":
        # Access morpheme prohibition properties
        morph = prohib.MorphemeRA
    elif class_name == "MoAdhocProhibAllomorph":
        # Access allomorph prohibition properties
        allo = prohib.AllomorphRA
```

Users must:
- Check ClassName explicitly
- Know which properties exist on which types
- Cast manually (implicit in pythonnet)
- Handle type mismatches carefully

---

## The Solution: AdhocProhibition Wrapper

Flexicon v2.3 provides `AdhocProhibition`, a transparent wrapper that handles all three types.

### Basic Usage

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("my project")

# Get all prohibitions - returns ProhibitionCollection
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()

# Access individual prohibitions
for prohib in prohibitions:
    # These work on ANY prohibition type
    print(f"Type: {prohib.prohibition_type}")
    print(f"GUID: {prohib.guid}")

    # Type-specific properties via intelligent routing
    if prohib.is_grammatical_prohibition:
        print(f"Feature: {prohib.FeatureRA}")
    elif prohib.is_morpheme_prohibition:
        print(f"Morpheme: {prohib.MorphemeRA}")
    elif prohib.is_allomorph_prohibition:
        print(f"Allomorph: {prohib.AllomorphRA}")

project.CloseProject()
```

---

## Prohibition Types

All three types inherit from IMoAdhocProhib. Flexicon provides convenience methods to check type:

### 1. Grammatical Feature Prohibitions (MoAdhocProhibGr)

Restrict which grammatical feature values can combine.

```python
if prohib.is_grammatical_prohibition:
    # Access grammatical-specific properties
    feature = prohib.FeatureRA
    feature_value = prohib.FeatureValueRA
    prohibited_value = prohib.ProhibitedFeatureValueRA

    print(f"Feature: {feature.Name.BestAnalysisAlternative.Text}")
    print(f"Cannot combine: {feature_value.Name} + {prohibited_value.Name}")
```

### 2. Morpheme Prohibitions (MoAdhocProhibMorph)

Restrict which morphemes can combine together.

```python
if prohib.is_morpheme_prohibition:
    # Access morpheme-specific properties
    morpheme = prohib.MorphemeRA
    prohibited = prohib.ProhibitedMorphemeRA

    print(f"Morpheme: {morpheme.ShortName}")
    print(f"Cannot combine with: {prohibited.ShortName}")
```

### 3. Allomorph Prohibitions (MoAdhocProhibAllomorph)

Restrict which allomorph variants can combine.

```python
if prohib.is_allomorph_prohibition:
    # Access allomorph-specific properties
    allomorph = prohib.AllomorphRA
    prohibited = prohib.ProhibitedAllomorphRA

    print(f"Allomorph: {allomorph.Form.BestVernacularAlternative.Text}")
    print(f"Cannot combine with: {prohibited.Form.BestVernacularAlternative.Text}")
```

---

## Filtering Collections

### Filter by Type

```python
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()

# Get only grammatical prohibitions
grammatical = prohibitions.grammatical_prohibitions()

# Get only morpheme prohibitions
morpheme = prohibitions.morpheme_prohibitions()

# Get only allomorph prohibitions
allomorph = prohibitions.allomorph_prohibitions()

# All return new ProhibitionCollection objects
print(f"Found {len(grammatical)} grammatical prohibitions")
print(f"Found {len(morpheme)} morpheme prohibitions")
print(f"Found {len(allomorph)} allomorph prohibitions")
```

### Filter by Property

Use `where()` for custom filtering:

```python
# Find prohibitions with specific properties
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()

# Grammatical prohibitions only
grammar_only = prohibitions.where(lambda p: p.is_grammatical_prohibition)

# Morpheme prohibitions that reference a specific morpheme
specific = prohibitions.where(
    lambda p: p.is_morpheme_prohibition and
    p.MorphemeRA.Guid == target_guid
)

# Multi-condition filtering
complex_filter = prohibitions.where(
    lambda p: (p.is_morpheme_prohibition or p.is_allomorph_prohibition) and
    p.guid is not None
)
```

### Chainable Filtering

Filters return new collections, allowing chaining:

```python
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()

# Chain type filter with custom filter
result = (prohibitions
    .grammatical_prohibitions()
    .where(lambda p: p.FeatureRA is not None))

# Chain multiple custom filters
result = (prohibitions
    .where(lambda p: p.is_morpheme_prohibition)
    .where(lambda p: p.MorphemeRA is not None))
```

---

## Collection Display

`ProhibitionCollection` shows type breakdown on display:

```python
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()
print(prohibitions)

# Output:
# ProhibitionCollection (12 items)
#   MoAdhocProhibGr: 5 (42%)
#   MoAdhocProhibMorph: 4 (33%)
#   MoAdhocProhibAllomorph: 3 (25%)
```

This helps you understand the composition of your prohibition set at a glance.

---

## Accessing Concrete Interfaces (Advanced)

For users who need direct access to the C# interface:

```python
prohib = prohibitions[0]

# Check type and get concrete interface
if prohib.is_morpheme_prohibition:
    concrete = prohib.as_morpheme_prohibition()
    # Now can access C# interface directly if needed
    morpheme_ra = concrete.MorphemeRA
```

---

## Before/After Comparison

### Before v2.3 (Raw API)

```python
# Get prohibitions - returns raw iterator
prohibs = project.MorphRules.GetAllAdhocCoProhibitions()

# Manual type checking needed
morpheme_count = 0
for prohib in prohibs:
    if prohib.ClassName == "MoAdhocProhibMorph":
        morpheme_count += 1
        morph = prohib.MorphemeRA  # Manual casting conceptually
        prohibited = prohib.ProhibitedMorphemeRA
        print(f"{morph.ShortName} -> {prohibited.ShortName}")

# Type breakdown requires manual counting
class_breakdown = {}
for prohib in project.MorphRules.GetAllAdhocCoProhibitions():
    class_name = prohib.ClassName
    class_breakdown[class_name] = class_breakdown.get(class_name, 0) + 1
```

### After v2.3 (Wrapper API)

```python
# Get prohibitions - returns smart collection
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()

# Built-in filtering
morpheme_prohibitions = prohibitions.morpheme_prohibitions()
print(f"Found {len(morpheme_prohibitions)} morpheme prohibitions")

# Access properties directly - type-safe routing
for prohib in morpheme_prohibitions:
    print(f"{prohib.MorphemeRA.ShortName} -> {prohib.ProhibitedMorphemeRA.ShortName}")

# Type breakdown on display
print(prohibitions)
# ProhibitionCollection (12 items)
#   MoAdhocProhibGr: 5 (42%)
#   MoAdhocProhibMorph: 4 (33%)
#   MoAdhocProhibAllomorph: 3 (25%)
```

---

## Common Patterns

### Get All Morpheme Prohibitions

```python
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()
morpheme_prohibitions = prohibitions.morpheme_prohibitions()
```

### Count by Type

```python
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()
print(f"Total: {len(prohibitions)}")
print(f"Grammatical: {len(prohibitions.grammatical_prohibitions())}")
print(f"Morpheme: {len(prohibitions.morpheme_prohibitions())}")
print(f"Allomorph: {len(prohibitions.allomorph_prohibitions())}")
```

### Find Prohibitions Referencing Specific Item

```python
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()

# Find morpheme prohibitions for a specific morpheme
target_morpheme = morphOps.Find("stem-past")
matching = prohibitions.where(
    lambda p: p.is_morpheme_prohibition and
    p.MorphemeRA.Guid == target_morpheme.Guid
)

# Find grammatical prohibitions for a feature
target_feature = gramOps.Find("tense")
matching = prohibitions.where(
    lambda p: p.is_grammatical_prohibition and
    p.FeatureRA.Guid == target_feature.Guid
)
```

### Iterate All Prohibitions with Type Handling

```python
prohibitions = project.MorphRules.GetAllAdhocCoProhibitions()

for prohib in prohibitions:
    print(f"Prohibition ({prohib.prohibition_type})")
    print(f"  GUID: {prohib.guid}")

    # Type-specific properties accessed transparently
    if prohib.is_grammatical_prohibition:
        print(f"  Feature: {prohib.FeatureRA}")
    elif prohib.is_morpheme_prohibition:
        print(f"  Morpheme: {prohib.MorphemeRA}")
    elif prohib.is_allomorph_prohibition:
        print(f"  Allomorph: {prohib.AllomorphRA}")
```

---

## Collection Methods

### `filter(prohibition_type=None, where=None)`

Filter collection by type or custom predicate.

```python
# By type name
collection.filter(prohibition_type="Grammatical")
collection.filter(prohibition_type="Morpheme")
collection.filter(prohibition_type="Allomorph")

# By abbreviation (case-insensitive)
collection.filter(prohibition_type="Gr")
collection.filter(prohibition_type="Morph")
collection.filter(prohibition_type="Allo")

# By custom predicate
collection.filter(where=lambda p: p.guid is not None)
```

### `where(predicate)`

Custom filtering with predicate function.

```python
# Single condition
collection.where(lambda p: p.is_morpheme_prohibition)

# Multiple conditions
collection.where(lambda p: (p.is_morpheme_prohibition or
                             p.is_allomorph_prohibition) and
                            p.guid is not None)
```

### `grammatical_prohibitions()`

Get grammatical prohibitions only.

```python
grammatical = collection.grammatical_prohibitions()
```

### `morpheme_prohibitions()`

Get morpheme prohibitions only.

```python
morpheme = collection.morpheme_prohibitions()
```

### `allomorph_prohibitions()`

Get allomorph prohibitions only.

```python
allomorph = collection.allomorph_prohibitions()
```

---

## Wrapper Properties

### `class_type`

Get the ClassName (concrete type identifier).

```python
prohib.class_type  # "MoAdhocProhibGr", "MoAdhocProhibMorph", etc.
```

### `guid`

Get the GUID as a string.

```python
prohib.guid  # "12345678-1234-1234-1234-123456789012"
```

### `prohibition_type`

Get human-readable type name.

```python
prohib.prohibition_type  # "Grammatical", "Morpheme", "Allomorph", or "Unknown"
```

### Capability Checks

```python
prohib.is_grammatical_prohibition  # bool
prohib.is_morpheme_prohibition     # bool
prohib.is_allomorph_prohibition    # bool
```

### Casting Methods

```python
concrete_gr = prohib.as_grammatical_prohibition()    # IMoAdhocProhibGr or None
concrete_m = prohib.as_morpheme_prohibition()        # IMoAdhocProhibMorph or None
concrete_a = prohib.as_allomorph_prohibition()       # IMoAdhocProhibAllomorph or None
```

---

## Backward Compatibility

The wrapper is fully backward compatible. Existing code continues to work unchanged:

```python
# Old code still works
for prohib in project.MorphRules.GetAllAdhocCoProhibitions():
    # Now returns AdhocProhibition wrapper instead of raw object
    # But supports the same properties
    if prohib.ClassName == "MoAdhocProhibMorph":
        # This still works
        pass
```

The only change is that `GetAllAdhocCoProhibitions()` now returns a `ProhibitionCollection` instead of a raw iterator, but `ProhibitionCollection` is iterable so existing iteration code continues to work.

---

## API Reference

### AdhocProhibition

Wrapper class for ad hoc morphosyntactic prohibition objects.

**Properties:**
- `class_type: str` - ClassName (concrete type)
- `guid: str` - GUID as string
- `prohibition_type: str` - Human-readable type
- `is_grammatical_prohibition: bool` - Check if grammatical type
- `is_morpheme_prohibition: bool` - Check if morpheme type
- `is_allomorph_prohibition: bool` - Check if allomorph type

**Methods:**
- `as_grammatical_prohibition()` - Cast to grammatical if applicable
- `as_morpheme_prohibition()` - Cast to morpheme if applicable
- `as_allomorph_prohibition()` - Cast to allomorph if applicable
- `get_property(name, default=None)` - Safe property access

### ProhibitionCollection

Smart collection for prohibitions with type-aware filtering.

**Properties:**
- Supports standard Python collection operations:
  - `len(collection)` - Number of items
  - `collection[index]` - Item access
  - `collection[start:end]` - Slicing
  - `for item in collection` - Iteration

**Methods:**
- `filter(prohibition_type=None, where=None)` - Filter by type or predicate
- `where(predicate)` - Custom filtering
- `grammatical_prohibitions()` - Get grammatical only
- `morpheme_prohibitions()` - Get morpheme only
- `allomorph_prohibitions()` - Get allomorph only

---

## Testing

Tests verify:
- Wrapper initialization with all three types
- GUID and type access
- Capability checks and type detection
- Safe casting methods
- Collection creation, iteration, and filtering
- Chainable filtering
- String representation
- Backward compatibility

Run tests:
```bash
pytest tests/test_prohibition_wrappers.py -v
```

---

## Related Classes

- `LCMObjectWrapper` - Base class for all wrappers
- `SmartCollection` - Base class for smart collections
- `MorphRuleOperations` - Access prohibitions via `GetAllAdhocCoProhibitions()`
- `AdhocProhibition` - Individual prohibition wrapper

---

## See Also

- [Phonological Rules Usage](USAGE_PHONRULES.md) - Similar wrapper pattern
- [Compound Rules Usage](USAGE_COMPOUND_RULES.md) - Another morphological rule type
- [API_DESIGN_USER_CENTRIC.md](API_DESIGN_USER_CENTRIC.md) - Design philosophy

