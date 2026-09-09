# Phonological Contexts in Flexicon

Phonological contexts describe the environments where phonological rules apply. Flexicon provides wrapper classes and smart collections to work with contexts transparently across their multiple concrete types.

## Context Types

Phonological contexts in FieldWorks can have multiple concrete implementations:

| Type | Purpose |
|------|---------|
| `PhSimpleContextSeg` | Simple context with single segment |
| `PhSimpleContextNC` | Simple context with natural class |
| `PhComplexContextSeg` | Complex context with multiple segment specifications |
| `PhComplexContextNC` | Complex context with multiple natural class specifications |
| `PhBoundaryContext` | Word or morpheme boundary context |

All types share a common base interface, but have different properties.

## Basic Usage: Before Wrappers

Without wrappers, working with contexts required type checking and casting:

```python
from flexicon import FLExProject

project = FLExProject('TestProject')
phonRuleOps = project.grammar.phonological_rules

# Get a rule
rule = phonRuleOps.GetAll()[0]

# Access input contexts (typed as base interface)
contexts = rule.StrucDescOS  # Raw access, requires manual type checking

# Work with contexts - tedious and error-prone
for context in contexts:
    class_name = context.ClassName

    if class_name == 'PhSimpleContextSeg':
        # Need to cast to concrete interface
        seg_context = IPhSimpleContextSeg(context)
        segment = seg_context.SegmentRA
        print(f"Segment: {segment.Name}")

    elif class_name == 'PhBoundaryContext':
        # Different type, different cast
        boundary_context = IPhBoundaryContext(context)
        btype = boundary_context.Type
        print(f"Boundary type: {btype}")

    # Other context types...
    # No type breakdown or filtering available
```

## Basic Usage: With Wrappers

With the `PhonologicalContext` wrapper and `ContextCollection`, work is simpler and more intuitive:

```python
from flexicon import FLExProject

project = FLExProject('TestProject')
phonRuleOps = project.grammar.phonological_rules

# Get a rule
rule = phonRuleOps.GetAll()[0]

# Access input contexts - returns smart collection
contexts = rule.input_contexts  # Returns ContextCollection

# Print type breakdown
print(contexts)
# Output:
# ContextCollection (8 total)
#   PhSimpleContextSeg: 4 (50%)
#   PhBoundaryContext: 3 (37%)
#   PhSimpleContextNC: 1 (13%)

# Iterate with transparent type access
for context in contexts:
    print(f"Context: {context.context_name}")

    # Check type with simple boolean properties
    if context.is_simple_context_seg:
        segment = context.segment
        print(f"  Segment: {segment.Name}")

    if context.is_boundary_context:
        btype = context.boundary_type
        print(f"  Boundary type: {btype}")
```

## Filtering Contexts

### Filter by Context Type

```python
rule = phonRuleOps.GetAll()[0]
contexts = rule.input_contexts

# Get only simple contexts
simple = contexts.simple_contexts()
print(f"Found {len(simple)} simple contexts")

# Get only segment contexts
seg_only = contexts.simple_context_seg()

# Get only natural class contexts
nc_only = contexts.simple_context_nc()

# Get only complex contexts
complex_only = contexts.complex_contexts()

# Get only boundary contexts
boundaries = contexts.boundary_contexts()

# Get both simple AND complex contexts
simple_and_complex = contexts.simple_contexts().extend(
    contexts.complex_contexts()
)
```

### Filter by Name

```python
contexts = rule.input_contexts

# Find contexts by name
word_contexts = contexts.filter(name_contains='word')
syllable_contexts = contexts.filter(name_contains='syllable')
```

### Chain Filters

```python
contexts = rule.input_contexts

# Chain multiple filters
result = (contexts
    .simple_contexts()
    .filter(name_contains='voiceless'))

# Returns contexts that are:
# 1. Simple contexts (segment or natural class)
# 2. Have 'voiceless' in their name
```

### Custom Filtering

```python
contexts = rule.input_contexts

# Use where() for complex conditions
voiceless_segments = contexts.where(
    lambda c: c.is_simple_context_seg and 'voiceless' in c.context_name
)

# Complex predicates
boundary_or_voiceless = contexts.where(
    lambda c: c.is_boundary_context or 'voiceless' in c.context_name
)
```

## Context Properties

### Common Properties (All Context Types)

All context types share these properties:

```python
context = rule.input_contexts[0]

# Context identification
name = context.context_name       # str - context name/identifier
description = context.description # str - context description

# Type checking
is_simple = context.is_simple_context      # bool - simple segment or NC
is_complex = context.is_complex_context    # bool - complex segment or NC
is_boundary = context.is_boundary_context  # bool - boundary

# Raw class type (for advanced use)
class_name = context.class_type  # str - e.g., "PhSimpleContextSeg"
```

### Type-Specific Properties

Access type-specific properties based on context type:

```python
context = rule.input_contexts[0]

# Simple segment context
if context.is_simple_context_seg:
    segment = context.segment  # IPhSegment object
    if segment:
        print(f"Segment: {segment.Name}")

# Simple natural class context
if context.is_simple_context_nc:
    nat_class = context.natural_class  # IPhNaturalClass object
    if nat_class:
        print(f"Natural class: {nat_class.Name}")

# Boundary context
if context.is_boundary_context:
    btype = context.boundary_type  # int - 0=word, 1=morpheme, etc.
    print(f"Boundary type: {btype}")
```

### Availability Pattern

Properties follow a consistent pattern:

```python
# Check if property is available
if context.is_simple_context_seg:
    # Property is guaranteed to work here
    seg = context.segment

# Safe access - returns None if not applicable
seg = context.segment if context.is_simple_context_seg else None
nc = context.natural_class if context.is_simple_context_nc else None
```

## Backward Compatibility

Wrapped contexts are fully transparent to existing code:

```python
# Old code: accessing through wrapper still works
rule = phonRuleOps.GetAll()[0]
contexts = rule.input_contexts

# Can still iterate over raw StrucDescOS if needed
# (though .input_contexts is recommended)
for ctx in rule.StrucDescOS:
    # ctx is still the raw LCM object
    pass

# New code: use wrapped contexts
for ctx in rule.input_contexts:
    # ctx is a PhonologicalContext wrapper
    if ctx.is_simple_context_seg:
        segment = ctx.segment
```

## Advanced Usage: Direct Interface Access

For power users who need direct C# interface access:

```python
context = rule.input_contexts[0]

# Check which type, then access concrete interface
if context.is_simple_context_seg:
    concrete = context.as_simple_context_seg()
    # concrete is now IPhSimpleContextSeg
    segment_ref = concrete.SegmentRA

    # Can call methods on concrete interface
    # (if any exist)

elif context.is_boundary_context:
    concrete = context.as_boundary_context()
    # concrete is now IPhBoundaryContext

# Or get concrete directly
concrete = context.concrete
# Same as above but without type safety
```

## Collection Operations

### Display Type Breakdown

```python
contexts = rule.input_contexts

# Automatic display of type distribution
print(contexts)
# Output:
# ContextCollection (12 total)
#   PhSimpleContextSeg: 6 (50%)
#   PhBoundaryContext: 4 (33%)
#   PhSimpleContextNC: 2 (17%)
```

### Iteration and Indexing

```python
contexts = rule.input_contexts

# Iterate
for ctx in contexts:
    print(ctx.context_name)

# Index
first_ctx = contexts[0]

# Slice
first_three = contexts[0:3]  # Returns new ContextCollection
```

### Collection Modification

```python
from flexicon.code.System.context_collection import ContextCollection
from flexicon.code.System.phonological_context import PhonologicalContext

contexts = ContextCollection()

# Add items
contexts.append(wrapped_context)
contexts.extend([ctx1, ctx2, ctx3])

# Clear
contexts.clear()
```

## Examples

### Example 1: Find All Boundary Contexts in a Rule

```python
rule = phonRuleOps.GetAll()[0]

boundaries = rule.input_contexts.boundary_contexts()
print(f"Rule '{rule.name}' has {len(boundaries)} boundary contexts")

for boundary in boundaries:
    btype = boundary.boundary_type
    if btype == 0:
        print("  Word boundary")
    elif btype == 1:
        print("  Morpheme boundary")
```

### Example 2: Filter Contexts by Type and Name

```python
rule = phonRuleOps.GetAll()[0]

# Find simple segment contexts with 'voiceless' in the name
voiceless_segments = (rule.input_contexts
    .simple_context_seg()
    .filter(name_contains='voiceless'))

for vctx in voiceless_segments:
    segment = vctx.segment
    print(f"Voiceless segment: {segment.Name}")
```

### Example 3: Analyze Context Diversity

```python
rule = phonRuleOps.GetAll()[0]

# Show what context types this rule uses
print(f"Rule: {rule.name}")
print(rule.input_contexts)

# Count each type
simple_seg = len(rule.input_contexts.simple_context_seg())
simple_nc = len(rule.input_contexts.simple_context_nc())
complex_seg = len(rule.input_contexts.complex_context_seg())
complex_nc = len(rule.input_contexts.complex_context_nc())
boundaries = len(rule.input_contexts.boundary_contexts())

print(f"Simple segments: {simple_seg}")
print(f"Simple NCs: {simple_nc}")
print(f"Complex segments: {complex_seg}")
print(f"Complex NCs: {complex_nc}")
print(f"Boundaries: {boundaries}")
```

### Example 4: Process Each Context Type

```python
rule = phonRuleOps.GetAll()[0]

for context in rule.input_contexts:
    if context.is_simple_context_seg:
        # Process simple segment context
        segment = context.segment
        print(f"Segment: {segment.Name}")

    elif context.is_simple_context_nc:
        # Process simple natural class context
        nat_class = context.natural_class
        print(f"Natural class: {nat_class.Name}")

    elif context.is_boundary_context:
        # Process boundary context
        btype = context.boundary_type
        print(f"Boundary (type {btype})")

    elif context.is_complex_context:
        # Process complex context
        print(f"Complex context: {context.context_name}")
```

## API Reference

### PhonologicalContext Class

Located in: `flexicon.code.System.phonological_context`

```python
class PhonologicalContext(LCMObjectWrapper):
    # Properties
    context_name: str           # Context name/identifier
    description: str            # Context description

    # Type checks (boolean properties)
    is_simple_context_seg: bool   # True if PhSimpleContextSeg
    is_simple_context_nc: bool    # True if PhSimpleContextNC
    is_simple_context: bool       # True if any simple context
    is_complex_context_seg: bool  # True if PhComplexContextSeg
    is_complex_context_nc: bool   # True if PhComplexContextNC
    is_complex_context: bool      # True if any complex context
    is_boundary_context: bool     # True if PhBoundaryContext

    # Type-specific properties
    segment: object          # IPhSegment (for simple segment contexts)
    natural_class: object    # IPhNaturalClass (for simple NC contexts)
    boundary_type: int       # Type value (for boundary contexts)

    # Advanced access
    concrete: object         # Raw concrete interface object

    # Advanced methods
    as_simple_context_seg(): IPhSimpleContextSeg or None
    as_simple_context_nc(): IPhSimpleContextNC or None
    as_complex_context_seg(): IPhComplexContextSeg or None
    as_complex_context_nc(): IPhComplexContextNC or None
    as_boundary_context(): IPhBoundaryContext or None
```

### ContextCollection Class

Located in: `flexicon.code.System.context_collection`

```python
class ContextCollection(SmartCollection):
    # Convenience type filters
    simple_contexts(): ContextCollection
    simple_context_seg(): ContextCollection
    simple_context_nc(): ContextCollection
    complex_contexts(): ContextCollection
    complex_context_seg(): ContextCollection
    complex_context_nc(): ContextCollection
    boundary_contexts(): ContextCollection

    # Filtering
    filter(name_contains=None, where=None): ContextCollection
    where(predicate): ContextCollection
    by_type(class_name): ContextCollection

    # Collection operations
    __iter__(), __len__(), __getitem__()
    append(item), extend(items), clear()
```

## See Also

- [PhonologicalRule Wrapper Documentation](USAGE_RULES.md) - For working with rules and their contexts
- [Smart Collections Pattern](API_DESIGN_USER_CENTRIC.md#smart-collections-pattern) - Design principles
- [LCMObjectWrapper](API_DESIGN_USER_CENTRIC.md#wrapper-classes-pattern) - Base wrapper class
