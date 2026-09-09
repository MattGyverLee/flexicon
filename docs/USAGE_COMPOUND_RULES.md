# Compound Rules: Phase 2 Wrapper Implementation

## Overview

This guide covers using the **CompoundRule** wrapper and **CompoundRuleCollection** smart collection in Flexicon v2.3. These wrappers transparently handle compound rules without exposing ClassName or casting complexity.

## The Problem: Type Complexity Without Wrappers

Before wrappers, accessing compound rules required manual type checking and casting:

```python
# WITHOUT wrappers (error-prone)
for rule in morphRuleOps.GetAll():
    if rule.ClassName == 'MoEndoCompound':
        # Cast to concrete interface
        concrete = IMoEndoCompound(rule)
        head_dep = concrete.LeftHeadDep
    elif rule.ClassName == 'MoExoCompound':
        # Different concrete type
        concrete = IMoExoCompound(rule)
        head_dep = concrete.RightHeadDep
```

## The Solution: Transparent Wrappers

Wrappers hide this complexity completely:

```python
# WITH wrappers (clean and safe)
for rule in morphRuleOps.GetAll():
    # Works on ALL compound rule types automatically
    print(f"Rule: {rule.name}")

    if rule.is_endo_compound:
        print("Head is internal")
    elif rule.is_exo_compound:
        print("Head is external")

    print(f"Head dependency: {rule.head_dependency}")
```

## Compound Rule Types

Flexicon supports two concrete compound rule types:

| Type | Class Name | Head Location |
|------|-----------|---------------|
| Endocentric | `MoEndoCompound` | Internal (within compound) |
| Exocentric | `MoExoCompound` | External (outside compound) |

Both types share common properties:
- `Name` - Rule name
- `LeftHeadDep` - Left head dependency
- `RightHeadDep` - Right head dependency
- `LeftContextOA` - Left phonological context
- `RightContextOA` - Right phonological context

## CompoundRule Wrapper

### Accessing Common Properties

All compound rule types expose these common properties:

```python
from flexicon.code.Grammar.compound_rule import CompoundRule

# Get a rule from operations
rule = morphRuleOps.GetAll()[0]
wrapped = CompoundRule(rule)

# Common properties (work on all types)
print(wrapped.name)                    # Rule name
print(wrapped.left_head_dep)          # Left head dependency
print(wrapped.right_head_dep)         # Right head dependency
print(wrapped.head_dependency)        # Either left or right (convenience)
print(wrapped.left_context)           # Left phonological context
print(wrapped.right_context)          # Right phonological context
print(wrapped.contexts)               # Both as tuple (left, right)
```

### Type Checking Properties

Use capability properties to check the rule type:

```python
# Check type (without accessing ClassName)
if wrapped.is_endo_compound:
    print("This is an endocentric compound")

if wrapped.is_exo_compound:
    print("This is an exocentric compound")
```

### Advanced: Direct C# Interface Access

For power users who need low-level access:

```python
# Optional: Cast to concrete C# interface if needed
if wrapped.as_endo_compound():
    concrete = wrapped.as_endo_compound()
    # Now can call methods/access properties not in wrapper
    # Most users won't need this

# Or get the concrete interface directly
concrete = wrapped.concrete
# Bypasses wrapper completely (use only if necessary)
```

## CompoundRuleCollection Smart Collection

### Overview

`GetAll()` returns a `CompoundRuleCollection` that manages compound rules while showing type diversity.

```python
from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

# GetAll returns CompoundRuleCollection
rules = morphRuleOps.GetAll()

# Displays type breakdown
print(rules)
# CompoundRuleCollection (8 total)
#   MoEndoCompound: 5 (62%)
#   MoExoCompound: 3 (38%)
```

### Filtering by Type

**Convenience methods** for filtering to specific concrete types:

```python
# Get only endocentric compounds
endo_rules = rules.endo_compounds()
print(f"Found {len(endo_rules)} endocentric rules")

# Get only exocentric compounds
exo_rules = rules.exo_compounds()
print(f"Found {len(exo_rules)} exocentric rules")

# Or use by_type() for explicit control
specific_type = rules.by_type('MoEndoCompound')
```

### Filtering by Properties

The `filter()` method supports common properties:

```python
# Filter by name (case-sensitive substring match)
verb_rules = rules.filter(name_contains='Verb')

# Filter by head dependency
lhs_head = rules.filter(head_dependency=0)

# Combine multiple criteria (AND logic)
result = rules.filter(name_contains='Verb', head_dependency=0)
```

### Custom Filtering with where()

For complex filtering, use `where()` with a predicate function:

```python
# Filter where both contexts are defined
full_context = rules.where(
    lambda r: r.left_context is not None and r.right_context is not None
)

# Filter by type AND other criteria
endo_with_name = rules.where(
    lambda r: r.is_endo_compound and 'Verb' in r.name
)

# Multiple conditions
complex = rules.where(
    lambda r: r.is_endo_compound and
              r.head_dependency == 0 and
              r.left_context is not None
)
```

### Chaining Filters

Filters return new collections, so you can chain them:

```python
# Chain convenience methods with other filters
verb_endo = rules.endo_compounds().filter(name_contains='Verb')

# Multiple chained filters
complex_result = (rules
    .endo_compounds()
    .filter(name_contains='Verb')
    .filter(head_dependency=0))

# Mix where() with other filters
result = rules.where(lambda r: 'Verb' in r.name).endo_compounds()
```

### Iterating the Collection

```python
# Standard iteration
for rule in rules:
    print(f"{rule.name}: {rule.class_type}")

# Unpacking (if collection size known)
rule1, rule2, rule3 = rules[:3]

# Indexing and slicing
first = rules[0]
subset = rules[1:5]  # Returns new CompoundRuleCollection
```

### Collection Management

```python
# Check size
print(f"Total rules: {len(rules)}")
if len(rules) == 0:
    print("No rules found")

# Append items
rules.append(new_rule)

# Extend with multiple items
rules.extend([rule1, rule2, rule3])

# Clear all items
rules.clear()
```

## Complete Example: Analyzing Compound Rules

```python
from flexicon import FLExProject
from flexicon.code.Grammar.compound_rule import CompoundRule

# Open project
project = FLExProject('ProjectName')
morphOps = project.Grammar.MorphRules

# Get all compound rules
rules = morphOps.GetAll()

# Show summary
print(f"Total compound rules: {len(rules)}")
print(rules)  # Shows type breakdown

# Analyze endo vs exo
endo = rules.endo_compounds()
exo = rules.exo_compounds()

print(f"\nEndocentric: {len(endo)} rules")
for rule in endo:
    print(f"  - {rule.name} (head dep: {rule.head_dependency})")

print(f"\nExocentric: {len(exo)} rules")
for rule in exo:
    print(f"  - {rule.name} (head dep: {rule.head_dependency})")

# Find verb-related compounds with both contexts
verb_full = rules.where(
    lambda r: 'Verb' in r.name and
              r.left_context is not None and
              r.right_context is not None
)

print(f"\nVerb compounds with full context: {len(verb_full)}")
for rule in verb_full:
    print(f"  - {rule.name}")

# Advanced: Access concrete interfaces if needed
for rule in rules:
    if rule.as_endo_compound():
        # Do something specific with endo compounds
        concrete = rule.as_endo_compound()
        # Use concrete interface...
```

## Migration Guide: From Manual Type Checking

### Before (Manual Casting)

```python
# Old pattern - repetitive and error-prone
for rule in morphRuleOps.GetAll():
    if rule.ClassName == 'MoEndoCompound':
        concrete = IMoEndoCompound(rule)
        print(concrete.LeftHeadDep)
    elif rule.ClassName == 'MoExoCompound':
        concrete = IMoExoCompound(rule)
        print(concrete.RightHeadDep)
```

### After (Wrapper Pattern)

```python
# New pattern - clean and unified
from flexicon.code.Grammar.compound_rule import CompoundRule

rules = morphRuleOps.GetAll()
for rule in rules:
    print(rule.head_dependency)  # Works for all types!

    if rule.is_endo_compound:
        print("Endo rule")
```

### Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| Type checking | Check `ClassName` | Use `is_endo_compound` |
| Property access | Manual casting required | Automatic routing |
| Mixed collections | Complex to handle | Transparent |
| Filtering | Manual loops | Built-in `filter()` |
| Chaining | Not possible | Fully chainable |

## API Reference

### CompoundRule Class

**Properties:**
- `name` (str) - Rule name
- `left_head_dep` (int) - Left head dependency
- `right_head_dep` (int) - Right head dependency
- `head_dependency` (int) - Either left or right (convenience)
- `left_context` (IMoPhonContext) - Left context or None
- `right_context` (IMoPhonContext) - Right context or None
- `contexts` (tuple) - Both contexts as (left, right)
- `is_endo_compound` (bool) - Check if endocentric
- `is_exo_compound` (bool) - Check if exocentric
- `concrete` - Raw C# interface object
- `class_type` (str) - ClassName string

**Methods:**
- `as_endo_compound()` - Cast to IMoEndoCompound if applicable (returns None otherwise)
- `as_exo_compound()` - Cast to IMoExoCompound if applicable (returns None otherwise)

### CompoundRuleCollection Class

**Methods:**
- `filter(name_contains=None, head_dependency=None, where=None)` - Filter by properties
- `where(predicate)` - Filter by custom predicate function
- `endo_compounds()` - Get only MoEndoCompound rules
- `exo_compounds()` - Get only MoExoCompound rules
- `by_type(class_name)` - Filter to specific concrete type
- `append(item)` - Add a rule
- `extend(items)` - Add multiple rules
- `clear()` - Remove all rules

**Standard Collection Methods:**
- `__iter__()` - Iteration support
- `__len__()` - Length support
- `__getitem__(index)` - Indexing and slicing
- `__str__()` - Type breakdown display

## Testing

Tests are located in `tests/test_compound_rule_wrappers.py` and cover:

- Collection creation and iteration
- Type filtering and breakdown
- Name and property filtering
- Custom predicate filtering
- Chaining multiple filters
- Wrapper property access
- Type checking (is_endo_compound, etc.)
- Advanced casting methods

Run tests:
```bash
pytest tests/test_compound_rule_wrappers.py -v
```

## Design Philosophy

This implementation follows the **Phase 2 (Phonological Rules)** pattern:

1. **Hide Interface Complexity** - Users never see IMoCompoundRule, casting, or ClassName
2. **Capability Checks** - `is_endo_compound`/`is_exo_compound` instead of manual type checking
3. **Unified Operations** - Same methods work across all concrete types
4. **Smart Collections** - Show type diversity while supporting unified filtering
5. **Optional Power Access** - Advanced users can access concrete interfaces if needed
6. **Type Breakdown Display** - Collections show composition when printed

## Related Documentation

- [API Design Philosophy](API_DESIGN_PHILOSOPHY.md) - Design principles
- [Phonological Rules Wrappers](USAGE_PHONOLOGICAL_RULES.md) - Similar pattern for phonology
- [Flexicon Architecture](README.rst) - Overall system design
