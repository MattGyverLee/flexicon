# Allomorph Wrappers Usage Guide

This guide demonstrates the Allomorph wrapper classes for simplified, type-transparent access to FLEx allomorphs.

## Overview

Allomorphs in FLEx have two concrete types with different properties:
- **MoStemAllomorph**: Variants of stems/roots (with StemName property)
- **MoAffixAllomorph**: Variants of affixes like prefixes and suffixes (with AffixType property)

The Allomorph wrapper transparently handles both types, providing unified access to common properties and type-specific properties without requiring manual casting or ClassName checking.

## Quick Start

### Before (Without Wrappers)

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("my_project", writeEnabled=False)

entry = project.LexiconAllEntries()[0]

# Get raw allomorphs - requires manual iteration
for allomorph in project.Allomorphs.GetAll(entry):
    # Access form using operations method
    form = project.Allomorphs.GetForm(allomorph)
    print(f"Form: {form}")

    # To check type or access type-specific properties, need casting
    if allomorph.ClassName == 'MoStemAllomorph':
        print(f"  Type: Stem")
        # Would need to manually cast to access StemName
    elif allomorph.ClassName == 'MoAffixAllomorph':
        print(f"  Type: Affix")
        # Would need to manually cast to access AffixType
```

### After (With Wrappers)

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("my_project", writeEnabled=False)

entry = project.LexiconAllEntries()[0]

# Get wrapped allomorphs - transparent type handling
allomorphs = project.Allomorphs.GetAll(entry)
print(allomorphs)  # Shows type breakdown

for allomorph in allomorphs:
    # Access form directly on wrapper
    print(f"Form: {allomorph.form}")

    # Check type with simple properties
    if allomorph.is_stem_allomorph:
        print(f"  Type: Stem")
        print(f"  Stem Name: {allomorph.stem_name}")
    elif allomorph.is_affix_allomorph:
        print(f"  Type: Affix")
        if allomorph.affix_type:
            print(f"  Affix Type: {allomorph.affix_type}")
```

## Basic Usage

### Getting Allomorphs

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("my_project")

# Get allomorphs for specific entry
entry = project.LexiconAllEntries()[0]
allomorphs = project.Allomorphs.GetAll(entry)

# Get ALL allomorphs in entire project
all_project_allomorphs = project.Allomorphs.GetAll()
```

### Viewing Type Breakdown

```python
allomorphs = project.Allomorphs.GetAll(entry)
print(allomorphs)
# Output:
# AllomorphCollection (8 total)
#   MoStemAllomorph: 5 (62%)
#   MoAffixAllomorph: 3 (38%)
```

### Accessing Common Properties

```python
for allomorph in allomorphs:
    # Form (text)
    print(f"Form: {allomorph.form}")

    # Phonological environments (list of IPhEnvironment)
    if allomorph.environment:
        print(f"Environments: {len(allomorph.environment)}")
        for env in allomorph.environment:
            print(f"  - {env.Name}")
    else:
        print("Appears in all contexts (no environment restriction)")

    # Gloss (usually empty for allomorphs)
    if allomorph.gloss:
        print(f"Gloss: {allomorph.gloss}")
```

### Checking Allomorph Type

```python
for allomorph in allomorphs:
    if allomorph.is_stem_allomorph:
        print(f"Stem allomorph: {allomorph.form}")
    elif allomorph.is_affix_allomorph:
        print(f"Affix allomorph: {allomorph.form}")
```

## Filtering

### Filter by Type

```python
# Get only stem allomorphs
stems = allomorphs.stem_allomorphs()
print(f"Found {len(stems)} stem allomorphs")

# Get only affix allomorphs
affixes = allomorphs.affix_allomorphs()
print(f"Found {len(affixes)} affix allomorphs")

# Equivalent to:
stems_alt = allomorphs.by_type('MoStemAllomorph')
affixes_alt = allomorphs.by_type('MoAffixAllomorph')
```

### Filter by Form

```python
# Find allomorphs with "-ing" in the form
ing_allomorphs = allomorphs.filter(form_contains='ing')
for allomorph in ing_allomorphs:
    print(f"Found: {allomorph.form}")

# Filter by environment
env = project.lp.PhonologicalDataOA.EnvironmentsOS[0]
env_allomorphs = allomorphs.filter(environment=env)
print(f"Found {len(env_allomorphs)} allomorphs with this environment")
```

### Custom Filtering

```python
# Find allomorphs with form length > 3
long_forms = allomorphs.where(lambda a: len(a.form) > 3)

# Find stem allomorphs with specific environments
complex_stems = allomorphs.where(
    lambda a: a.is_stem_allomorph and len(a.environment) > 0
)

# Find allomorphs without environments
unrestricted = allomorphs.where(lambda a: len(a.environment) == 0)
```

## Chaining Filters

One of the most powerful features of the wrapper is the ability to chain filters:

```python
# Find "-ing" forms that are affixes
ing_affixes = allomorphs.affix_allomorphs().filter(form_contains='ing')

# Find long stem forms
long_stems = allomorphs.stem_allomorphs().where(lambda a: len(a.form) > 4)

# Complex chain
restricted_stems = (allomorphs
    .stem_allomorphs()
    .filter(form_contains='a')
    .where(lambda a: len(a.environment) > 0)
)

for allomorph in restricted_stems:
    print(f"Found: {allomorph.form}")
```

## Displaying Results

### Simple Display

```python
allomorphs = project.Allomorphs.GetAll(entry)

# Show type breakdown
print(allomorphs)
# AllomorphCollection (8 total)
#   MoStemAllomorph: 5 (62%)
#   MoAffixAllomorph: 3 (38%)

# Count items
print(f"Total allomorphs: {len(allomorphs)}")

# Iterate
for allomorph in allomorphs:
    print(f"  - {allomorph.form} ({allomorph.class_type})")
```

### Detailed Display

```python
for allomorph in allomorphs:
    print(f"\nAllomorph: {allomorph.form}")
    print(f"  Type: {'Stem' if allomorph.is_stem_allomorph else 'Affix'}")
    print(f"  Class: {allomorph.class_type}")

    if allomorph.is_stem_allomorph:
        print(f"  Stem Name: {allomorph.stem_name}")
    elif allomorph.is_affix_allomorph:
        if allomorph.affix_type:
            print(f"  Affix Type: {allomorph.affix_type}")

    if allomorph.environment:
        print(f"  Environments ({len(allomorph.environment)}):")
        for env in allomorph.environment:
            print(f"    - {env.Name}")
    else:
        print("  Environments: (none - appears in all contexts)")
```

## Advanced: Direct Interface Access

For users who need advanced control and know C# interfaces, optional casting methods are available:

```python
for allomorph in allomorphs:
    # Cast to concrete interface if type matches
    if stem := allomorph.as_stem_allomorph():
        # Now can access IMoStemAllomorph-specific methods/properties
        print(f"Stem name: {stem.StemName}")

    if affix := allomorph.as_affix_allomorph():
        # Now can access IMoAffixAllomorph-specific methods/properties
        print(f"Affix type: {affix.AffixType}")

    # Direct access to concrete interface (bypasses wrapper)
    concrete = allomorph.concrete
    # Use concrete interface for advanced operations
```

## Real-World Examples

### Find Allomorphs Used in Parsing

```python
# Get all allomorphs that have phonological environment restrictions
restricted = allomorphs.where(lambda a: len(a.environment) > 0)
print(f"Allomorphs with environment restrictions: {len(restricted)}")

for allomorph in restricted:
    print(f"\n{allomorph.form}:")
    for env in allomorph.environment:
        print(f"  - {env.Name}")
```

### Organize by Type

```python
allomorphs = project.Allomorphs.GetAll(entry)

stems = allomorphs.stem_allomorphs()
affixes = allomorphs.affix_allomorphs()

print(f"Stems ({len(stems)}):")
for allo in stems:
    print(f"  - {allo.form}")

print(f"\nAffixes ({len(affixes)}):")
for allo in affixes:
    print(f"  - {allo.form}")
```

### Find Similar Forms

```python
# Find allomorphs similar to a target form
target = "walk"
similar = allomorphs.where(lambda a: target in a.form or a.form in target)

print(f"Forms similar to '{target}':")
for allo in similar:
    print(f"  - {allo.form}")
```

### Export Allomorph Summary

```python
allomorphs = project.Allomorphs.GetAll(entry)

print("Allomorph Summary")
print("=" * 50)
print(f"Entry: {entry.HeadwordRef.Form}")
print(f"Total allomorphs: {len(allomorphs)}\n")
print(allomorphs)
print("\nDetailed List:")

for allomorph in allomorphs:
    type_name = "Stem" if allomorph.is_stem_allomorph else "Affix"
    env_count = len(allomorph.environment)
    env_text = f"{env_count} environment(s)" if env_count else "unrestricted"
    print(f"  {allomorph.form:15} | {type_name:5} | {env_text}")
```

## Migration Guide

If you have existing code using raw allomorphs, here's how to migrate:

### Old Code
```python
for allomorph in project.Allomorphs.GetAll(entry):
    form = project.Allomorphs.GetForm(allomorph)
    print(form)
```

### New Code
```python
for allomorph in project.Allomorphs.GetAll(entry):
    print(allomorph.form)  # Direct access on wrapper
```

### Old Code with Type Checking
```python
for allomorph in project.Allomorphs.GetAll(entry):
    form = project.Allomorphs.GetForm(allomorph)
    if allomorph.ClassName == 'MoStemAllomorph':
        print(f"Stem: {form}")
    else:
        print(f"Affix: {form}")
```

### New Code with Type Checking
```python
for allomorph in project.Allomorphs.GetAll(entry):
    if allomorph.is_stem_allomorph:
        print(f"Stem: {allomorph.form}")
    else:
        print(f"Affix: {allomorph.form}")
```

## Common Patterns

### Filter and Count

```python
allomorphs = project.Allomorphs.GetAll(entry)

# Count by type
stem_count = len(allomorphs.stem_allomorphs())
affix_count = len(allomorphs.affix_allomorphs())

print(f"Stems: {stem_count}, Affixes: {affix_count}")
```

### Find Unspecified Allomorphs

```python
# Find allomorphs without environment restrictions
unspecified = allomorphs.where(lambda a: len(a.environment) == 0)
```

### Group by Environment

```python
from collections import defaultdict

env_groups = defaultdict(list)

for allomorph in allomorphs:
    if allomorph.environment:
        # Group by first environment
        env = allomorph.environment[0]
        env_groups[env.Name].append(allomorph)
    else:
        env_groups['(unrestricted)'].append(allomorph)

for env_name, allos in env_groups.items():
    print(f"\n{env_name}:")
    for allo in allos:
        print(f"  - {allo.form}")
```

## API Reference

### Allomorph Properties

- **form** (str): The allomorph form text
- **gloss** (str): The allomorph gloss (usually empty)
- **environment** (list): List of IPhEnvironment objects
- **is_stem_allomorph** (bool): True if MoStemAllomorph
- **is_affix_allomorph** (bool): True if MoAffixAllomorph
- **stem_name** (str): Stem name (stem allomorphs only)
- **affix_type** (IMoMorphType or None): Affix type (affix allomorphs only)
- **class_type** (str): The concrete type name ("MoStemAllomorph" or "MoAffixAllomorph")

### Allomorph Methods

- **as_stem_allomorph()**: Cast to IMoStemAllomorph if applicable
- **as_affix_allomorph()**: Cast to IMoAffixAllomorph if applicable

### AllomorphCollection Methods

- **filter(form_contains=None, environment=None, where=None)**: Filter by criteria
- **where(predicate)**: Filter by custom predicate function
- **stem_allomorphs()**: Get only stem allomorphs
- **affix_allomorphs()**: Get only affix allomorphs
- **by_type(class_name)**: Get allomorphs of specific concrete type

### AllomorphCollection Properties

- **len(collection)**: Total number of allomorphs
- **collection[index]**: Access item by index
- **collection[start:end]**: Slice collection
- **str(collection)**: Display type breakdown

## See Also

- AllomorphOperations: Operations for creating/modifying allomorphs
- Allomorph: Individual wrapper class
- AllomorphCollection: Smart collection class
- PhonologicalContext: Similar wrapper pattern for contexts
