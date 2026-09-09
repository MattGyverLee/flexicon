# Morphosyntactic Analysis (MSA) Usage Guide

This guide demonstrates how to work with morphosyntactic analyses (MSAs) using Flexicon's unified wrapper interface.

## What Are Morphosyntactic Analyses?

MSAs describe the grammatical properties of morphemes:
- **MoStemMsa**: A root or stem with its part of speech
- **MoDerivAffMsa**: A derivational affix that changes the part of speech
- **MoInflAffMsa**: An inflectional affix that adds grammatical features
- **MoUnclassifiedAffixMsa**: An affix with unknown derivational/inflectional status

## Before: Working Without Wrappers

Without the wrapper, you had to manually check types and cast:

```python
from flexicon.code.lcm_casting import cast_to_concrete, get_pos_from_msa

entry = project.lp.LexDB.Entries[0]

for msa in entry.MorphoSyntaxAnalysesOC:
    # Check type manually
    if msa.ClassName == 'MoStemMsa':
        # Cast to concrete type
        concrete = cast_to_concrete(msa)

        # Now can access type-specific properties
        pos = concrete.PartOfSpeechRA
        if pos:
            print(f"Stem POS: {pos.Name.BestAnalysisAlternative.Text}")

    elif msa.ClassName == 'MoDerivAffMsa':
        # Cast and access different properties
        concrete = cast_to_concrete(msa)
        from_pos = concrete.FromPartOfSpeechRA
        to_pos = concrete.ToPartOfSpeechRA
        if from_pos and to_pos:
            print(f"Derives {from_pos.Name} to {to_pos.Name}")
```

**Problems:**
- Boilerplate code for every MSA
- Easy to forget type checks
- Mixing type-specific logic throughout code
- No way to see MSA type distribution at a glance

## After: Working With Wrapper Classes

With wrappers, the same logic is clean and type-safe:

```python
from flexicon.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis
from flexicon.code.Lexicon.msa_collection import MSACollection

entry = project.lp.LexDB.Entries[0]

# Wrap MSAs
msas = MSACollection([
    MorphosyntaxAnalysis(msa) for msa in entry.MorphoSyntaxAnalysesOC
])

# See type breakdown
print(msas)
# MSACollection (8 total)
#   MoStemMsa: 4 (50%)
#   MoDerivAffMsa: 2 (25%)
#   MoInflAffMsa: 2 (25%)

# Filter by type
stem_msas = msas.stem_msas()
deriv_msas = msas.deriv_aff_msas()

# Access properties without casting
for msa in msas:
    if msa.is_stem_msa:
        pos = msa.pos_main
        if pos:
            print(f"Stem: {pos.Name.BestAnalysisAlternative.Text}")

    elif msa.is_deriv_aff_msa:
        from_pos = msa.pos_from
        to_pos = msa.pos_to
        if from_pos and to_pos:
            print(f"Derives {from_pos} to {to_pos}")
```

## Type Checking Patterns

### Checking if an MSA is a Specific Type

```python
for msa in msas:
    if msa.is_stem_msa:
        print("This is a stem")

    elif msa.is_deriv_aff_msa:
        print("This is a derivational affix")

    elif msa.is_infl_aff_msa:
        print("This is an inflectional affix")

    elif msa.is_unclassified_aff_msa:
        print("This is an unclassified affix")
```

### Getting POS Information

The wrapper provides unified access to part of speech:

```python
# All MSA types have a main POS
for msa in msas:
    pos = msa.pos_main
    if pos:
        print(f"Main POS: {pos.Name.BestAnalysisAlternative.Text}")

# Derivational affixes have input and output POS
for msa in msas.deriv_aff_msas():
    if msa.has_from_pos:
        from_pos = msa.pos_from
        to_pos = msa.pos_to
        print(f"{from_pos} -> {to_pos}")

    # Alternatively, use pos_to (same as pos_main for other types)
    output_pos = msa.pos_to
```

## Filtering Patterns

### Filter by Type

```python
# Get only specific MSA types
stem_only = msas.stem_msas()
deriv_only = msas.deriv_aff_msas()
infl_only = msas.infl_aff_msas()
unclass_only = msas.unclassified_aff_msas()

# Or use generic by_type()
specific = msas.by_type('MoStemMsa')
```

### Filter by POS Presence

```python
# MSAs with a POS assigned
with_pos = msas.filter(has_pos=True)

# MSAs without a POS
without_pos = msas.filter(has_pos=False)
```

### Filter by Specific POS

```python
# Get all MSAs for a particular POS
target_pos = project.lp.PartsOfSpeechOA.PossibilitiesOS[0]  # noun

matching = msas.filter(pos_main=target_pos)

for msa in matching:
    print(f"Has POS: {target_pos.Name.BestAnalysisAlternative.Text}")
```

### Custom Filtering

```python
# Derivational affixes with both input and output POS
complete_derivs = msas.where(
    lambda m: m.is_deriv_aff_msa and
              m.pos_from is not None and
              m.pos_to is not None
)

# Stems without POS (incomplete entries)
incomplete_stems = msas.stem_msas().filter(has_pos=False)

# Inflectional affixes for a specific POS
infl_for_noun = msas.infl_aff_msas().filter(pos_main=noun_pos)
```

## Chaining Filters

Filters return new collections, so you can chain them:

```python
# Find derivational affixes that create nouns
noun_creating = msas.deriv_aff_msas().filter(pos_main=noun_pos)

# Find stems with a specific POS that have MSAs
target_pos = ...
relevant_msas = msas.filter(pos_main=target_pos).stem_msas()

# Complex chain: inflectional affixes without POS
incomplete = msas.infl_aff_msas().filter(has_pos=False)
```

## Iteration Patterns

### Simple Iteration

```python
for msa in msas:
    print(f"Type: {msa.class_type}")
    if msa.pos_main:
        print(f"POS: {msa.pos_main.Name.BestAnalysisAlternative.Text}")
```

### Unpacking

```python
# Get first few MSAs
first, second, *rest = msas

# Get specific indices
first_stem = msas[0]
subset = msas[0:3]  # Returns new MSACollection
```

### Counting by Type

```python
print(f"Total MSAs: {len(msas)}")
print(f"Stems: {len(msas.stem_msas())}")
print(f"Derivational affixes: {len(msas.deriv_aff_msas())}")
```

## Working with Entry Operations

In typical usage, you'd get MSAs through entry operations:

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("my_project", writeEnabled=False)

# Get an entry (this would come from LexEntry operations)
entry = project.lp.LexDB.Entries[0]

# Wrap MSAs
msas = MSACollection([
    MorphosyntaxAnalysis(msa)
    for msa in entry.MorphoSyntaxAnalysesOC
])

# Use unified interface
print(msas)  # Type breakdown
stem_msas = msas.stem_msas()  # Filter

project.CloseProject()
```

## Advanced: Direct C# Interface Access

For power users who need to access C# interfaces directly:

```python
for msa in msas:
    # Get the concrete C# interface
    if msa.as_stem_msa():
        concrete = msa.as_stem_msa()
        # Can now use IMMoStemMsa-specific methods

    # Or access via .concrete property
    concrete = msa.concrete
    # Use concrete interface for advanced operations
```

**Note:** Most users should not need this. The wrapper properties (is_stem_msa, pos_main, etc.) cover the common use cases.

## Type-Specific Properties

### MoStemMsa (Stem Analysis)

```python
msa = msas.stem_msas()[0]

# Common properties (via wrapper)
print(msa.class_type)      # "MoStemMsa"
print(msa.is_stem_msa)     # True
print(msa.pos_main)        # The stem's part of speech

# For power users: advanced properties
concrete = msa.as_stem_msa()
if concrete:
    # Access IMoStemMsa-specific methods/properties
    pass
```

### MoDerivAffMsa (Derivational Affix)

```python
msa = msas.deriv_aff_msas()[0]

# Common properties
print(msa.is_deriv_aff_msa)    # True
print(msa.pos_from)            # Input POS (what it derives from)
print(msa.pos_to)              # Output POS (what it creates)
print(msa.has_from_pos)        # Check if both are set

# For power users
concrete = msa.as_deriv_aff_msa()
if concrete:
    # Access IMoDerivAffMsa-specific properties
    pass
```

### MoInflAffMsa (Inflectional Affix)

```python
msa = msas.infl_aff_msas()[0]

# Common properties
print(msa.is_infl_aff_msa)     # True
print(msa.pos_main)            # The POS this affix attaches to

# For power users
concrete = msa.as_infl_aff_msa()
if concrete:
    # Access IMoInflAffMsa-specific properties (slots, etc.)
    pass
```

### MoUnclassifiedAffixMsa

```python
msa = msas.unclassified_aff_msas()[0]

# Common properties
print(msa.is_unclassified_aff_msa)  # True
print(msa.pos_main)                  # The POS (if classified)

# For power users
concrete = msa.as_unclassified_aff_msa()
if concrete:
    # Access IMoUnclassifiedAffixMsa-specific properties
    pass
```

## Common Mistakes to Avoid

### [ERROR] Forgetting to Wrap

```python
# DON'T do this (old way)
for msa in entry.MorphoSyntaxAnalysesOC:
    # Can't use wrapper properties here
    print(msa.is_stem_msa)  # AttributeError!

# DO this instead
msas = MSACollection([
    MorphosyntaxAnalysis(msa) for msa in entry.MorphoSyntaxAnalysesOC
])
for msa in msas:
    print(msa.is_stem_msa)  # Works!
```

### [ERROR] Modifying Filtered Collections

```python
# Filtered collections are new objects
stem_msas = msas.stem_msas()

# Adding to filtered collection won't affect original
stem_msas.append(some_msa)

# To modify original, work with it directly
msas.append(some_msa)
```

### [ERROR] Accessing Type-Specific Properties Without Checking

```python
# DON'T do this
for msa in msas:
    print(msa.pos_from)  # AttributeError if not a derivational MSA!

# DO this instead
for msa in msas:
    if msa.is_deriv_aff_msa:
        print(msa.pos_from)  # Safe
    elif msa.has_from_pos:   # Alternative check
        print(msa.pos_from)
```

## Summary

The MSA wrapper provides:

| Task | Old Way | New Way |
|------|---------|---------|
| Check type | `if msa.ClassName == 'MoStemMsa':` | `if msa.is_stem_msa:` |
| Get POS | `cast_to_concrete(msa).PartOfSpeechRA` | `msa.pos_main` |
| Get deriv POS | `cast_to_concrete(msa).FromPartOfSpeechRA` | `msa.pos_from` |
| Filter by type | Manual loops | `msas.stem_msas()` |
| Filter by POS | Manual loops | `msas.filter(pos_main=target)` |
| See type counts | Manual counting | `print(msas)` |
| Cast for advanced | `cast_to_concrete(msa)` | `msa.concrete` or `msa.as_stem_msa()` |

The wrapper abstracts away the complexity of handling multiple MSA types while keeping the interface clean and intuitive.
