# Smart Collections Architecture Guide

## Overview

Smart collections are a fundamental pattern in Flexicon for presenting multiple concrete types in a unified way. They allow users to work with heterogeneous collections (objects of different types) naturally while still seeing type diversity and having the ability to filter by type.

This guide explains why smart collections exist, how they work, and how to create new ones for your domain.

---

## The Problem: Multiple Types in Collections

### Collections with Type Diversity

When you query FLEx for objects with multiple concrete implementations, you get a heterogeneous collection:

```python
# Get all phonological rules - but they have different types!
rules = phonRuleOps.GetAll()
# Returns rules that are:
#   - 7 PhRegularRule objects
#   - 3 PhMetathesisRule objects
#   - 2 PhReduplicationRule objects
# Total: 12 rules, but 3 different concrete types
```

This creates challenges for users:

1. **Type Visibility:** Users need to know what types are represented
2. **Type Filtering:** Users need to easily filter to specific types
3. **Unified Operations:** Users need to work across all types without casting

### The Collection Problem Without SmartCollection

```python
# Without smart collections, users would:
raw_rules = phonRuleOps.GetAll()

# No way to see type breakdown
print(f"Got {len(raw_rules)} rules")
# Output: "Got 12 rules" (no type information)

# Manual type checking to filter
regular_only = []
for rule in raw_rules:
    if rule.ClassName == 'PhRegularRule':
        regular_only.append(rule)

# Working with all types together is tedious
for rule in raw_rules:
    if rule.ClassName == 'PhRegularRule':
        print(rule.RightHandSidesOS)
    elif rule.ClassName == 'PhMetathesisRule':
        print(rule.LeftPartOfMetathesisOS)
    # ... more type checks
```

---

## The Solution: SmartCollection

Smart collections provide:

1. **Type Breakdown Display:** Show what types are in the collection
2. **Type Filtering:** Easily filter to specific types
3. **Custom Filtering:** Domain-specific filter methods
4. **Unified Interface:** Work seamlessly across all types

### How SmartCollection Solves the Problem

```python
# With smart collections, users experience:
rules = phonRuleOps.GetAll()  # Returns SmartCollection

# Type breakdown visible on display
print(rules)
# Output:
# PhonologicalRuleCollection (12 total)
#   PhRegularRule: 7 (58%)
#   PhMetathesisRule: 3 (25%)
#   PhReduplicationRule: 2 (17%)

# Easy type filtering
regular_only = rules.by_type('PhRegularRule')  # Returns 7-item collection
print(len(regular_only))  # 7

# Custom filtering (domain-specific)
voicing_rules = rules.filter(name_contains='voicing')
print(voicing_rules)  # Shows filtered breakdown
```

Much more user-friendly!

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User Code (GetAll returns SmartCollection)                  │
│                                                               │
│  rules = phonRuleOps.GetAll()                                │
│  print(rules)              # Shows type breakdown            │
│  voicing = rules.filter()  # Domain-specific filtering      │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  SmartCollection (Base Class)                                │
│                                                               │
│  - Stores _items list                                        │
│  - __str__() shows type breakdown                            │
│  - by_type() filters to single concrete type                │
│  - filter() abstract method for subclasses                  │
│  - Standard collection methods (__iter__, __len__)           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Domain-Specific Collection (RuleCollection)                 │
│                                                               │
│  - Overrides filter() with domain-specific logic             │
│  - filter(name_contains='voicing', direction='LTR')         │
│  - Inherits all SmartCollection behavior                    │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Wrapped Items (PhonologicalRule objects)                    │
│                                                               │
│  - Each item is a wrapper that handles its concrete type     │
│  - Transparent property access                               │
│  - Type checking via class_type property                     │
└─────────────────────────────────────────────────────────────┘
```

---

## SmartCollection Pattern

### Base SmartCollection

Flexicon provides `SmartCollection` as the base class:

```python
from flexicon.code.Shared.smart_collection import SmartCollection


class MyCollection(SmartCollection):
    """
    Collection of domain-specific objects with type awareness.

    Inherits from SmartCollection for standard collection operations
    and type-aware display.
    """

    def filter(self, **criteria):
        """
        Filter the collection using domain-specific criteria.

        Subclasses override this to implement filtering logic.

        Args:
            **criteria: Domain-specific filter parameters.

        Returns:
            MyCollection: New collection with filtered items.
        """
        # Subclasses implement filtering here
        raise NotImplementedError
```

### Key Features

#### 1. Standard Collection Methods

SmartCollection is a standard Python iterable:

```python
rules = phonRuleOps.GetAll()

# Iteration
for rule in rules:
    print(rule.Name)

# Length
print(f"Total rules: {len(rules)}")

# Indexing
first = rules[0]

# Slicing
first_three = rules[0:3]  # Returns new collection
print(type(first_three))  # RuleCollection (same type)

# Unpacking
first, second, *rest = rules
```

#### 2. Type Breakdown Display (__str__)

When printed, shows type distribution:

```python
rules = phonRuleOps.GetAll()

print(rules)
# Output:
# PhonologicalRuleCollection (12 total)
#   PhRegularRule: 7 (58%)
#   PhMetathesisRule: 3 (25%)
#   PhReduplicationRule: 2 (17%)

# Empty collections show clearly
empty_rules = rules.by_type('NonExistentType')
print(empty_rules)
# Output: PhonologicalRuleCollection (empty)
```

#### 3. Type Filtering (by_type)

Filter to a specific concrete type:

```python
rules = phonRuleOps.GetAll()

# Get just regular rules
regular = rules.by_type('PhRegularRule')
print(len(regular))  # 7
print(regular)  # Shows only PhRegularRule in breakdown

# Type filtering returns new collection (doesn't modify original)
assert len(rules) == 12  # Original unchanged
```

#### 4. Custom Filtering (filter)

Domain-specific filtering logic:

```python
rules = phonRuleOps.GetAll()

# Custom filter (defined in subclass)
voicing = rules.filter(name_contains='voicing')
print(voicing)  # Shows filtered type breakdown

# Chaining filters
regular_voicing = rules.by_type('PhRegularRule').filter(name_contains='voicing')
```

---

## Creating Domain-Specific Collections

### Pattern: Phonological Rules Collection

Here's a complete example:

```python
from flexicon.code.Shared.smart_collection import SmartCollection


class PhonologicalRuleCollection(SmartCollection):
    """
    Collection of phonological rules with type-aware filtering.

    Shows the distribution of rule types (Regular, Metathesis, Reduplication)
    and provides domain-specific filtering.

    Type breakdown displayed on print():
        PhonologicalRuleCollection (12 total)
          PhRegularRule: 7 (58%)
          PhMetathesisRule: 3 (25%)
          PhReduplicationRule: 2 (17%)
    """

    def __init__(self, items=None):
        """
        Initialize collection with phonological rules.

        Args:
            items: Iterable of PhonologicalRule objects, or None for empty.
        """
        super().__init__(items)

    def filter(self, name_contains=None, direction=None, **kwargs):
        """
        Filter rules by name and/or direction.

        Args:
            name_contains: Filter to rules with this text in their name.
            direction: Filter to rules with this direction ('LTR', 'RTL').
            **kwargs: Additional domain-specific filter parameters.

        Returns:
            PhonologicalRuleCollection: New collection with filtered items.

        Example::

            all_rules = phonRuleOps.GetAll()

            # Filter by name
            voicing = all_rules.filter(name_contains='voicing')
            print(voicing)  # Shows subset with type breakdown

            # Filter by direction
            ltr = all_rules.filter(direction='LTR')

            # Combine filters
            voicing_ltr = all_rules.filter(
                name_contains='voicing',
                direction='LTR'
            )

            # Chain filters (using by_type)
            regular_voicing = all_rules.by_type('PhRegularRule').filter(
                name_contains='voicing'
            )
        """
        filtered = self._items[:]  # Start with all items

        # Filter by name
        if name_contains:
            filtered = [
                rule for rule in filtered
                if name_contains.lower() in rule.Name.lower()
            ]

        # Filter by direction
        if direction:
            filtered = [
                rule for rule in filtered
                if rule.Direction == direction
            ]

        # Return new collection of same type
        return PhonologicalRuleCollection(filtered)

    def by_type_count(self):
        """
        Get count of items by type.

        Returns a dictionary mapping ClassName -> count.

        Example::

            rules = phonRuleOps.GetAll()
            counts = rules.by_type_count()
            # {'PhRegularRule': 7, 'PhMetathesisRule': 3, 'PhReduplicationRule': 2}
        """
        counts = {}
        for item in self._items:
            class_type = item.class_type
            counts[class_type] = counts.get(class_type, 0) + 1
        return counts

    def has_type(self, class_name):
        """
        Check if collection contains objects of a specific type.

        Args:
            class_name: The ClassName to check for.

        Returns:
            bool: True if at least one object of that type is present.

        Example::

            rules = phonRuleOps.GetAll()
            if rules.has_type('PhMetathesisRule'):
                print("Collection has metathesis rules")
        """
        return any(item.class_type == class_name for item in self._items)

    def regular_rules(self):
        """
        Get just the regular rules (convenience method).

        Returns:
            PhonologicalRuleCollection: Filtered to PhRegularRule only.
        """
        return self.by_type('PhRegularRule')

    def metathesis_rules(self):
        """
        Get just the metathesis rules (convenience method).

        Returns:
            PhonologicalRuleCollection: Filtered to PhMetathesisRule only.
        """
        return self.by_type('PhMetathesisRule')

    def reduplication_rules(self):
        """
        Get just the reduplication rules (convenience method).

        Returns:
            PhonologicalRuleCollection: Filtered to PhReduplicationRule only.
        """
        return self.by_type('PhReduplicationRule')
```

### Pattern: Lexical Entry Collection

Another example for a different domain:

```python
from flexicon.code.Shared.smart_collection import SmartCollection


class LexicalEntryCollection(SmartCollection):
    """
    Collection of lexical entries with filtering capabilities.

    Unlike phonological rules, entries don't have multiple concrete types,
    but collections are still useful for filtering and display.
    """

    def filter(self, gloss_contains=None, pos=None, **kwargs):
        """
        Filter entries by gloss and/or part of speech.

        Args:
            gloss_contains: Filter to entries with this text in glosses.
            pos: Filter to entries with this part of speech.

        Returns:
            LexicalEntryCollection: New filtered collection.
        """
        filtered = self._items[:]

        if gloss_contains:
            filtered = [
                e for e in filtered
                if any(gloss_contains.lower() in sense_gloss.lower()
                       for sense_gloss in e.get_all_glosses())
            ]

        if pos:
            filtered = [
                e for e in filtered
                if e.get_part_of_speech() == pos
            ]

        return LexicalEntryCollection(filtered)

    def by_pos(self):
        """
        Group entries by part of speech.

        Returns a dictionary mapping POS -> LexicalEntryCollection.

        Example::

            entries = entryOps.GetAll()
            by_pos = entries.by_pos()
            # {'noun': 45, 'verb': 32, 'adjective': 18}
        """
        groups = {}
        for entry in self._items:
            pos = entry.get_part_of_speech() or 'Unknown'
            if pos not in groups:
                groups[pos] = []
            groups[pos].append(entry)

        # Convert to collections
        return {
            pos: LexicalEntryCollection(items)
            for pos, items in groups.items()
        }
```

---

## Code Examples

### Example 1: Creating a Smart Collection

In an operations class:

```python
from flexicon.code.Grammar.phonological_rule_collection import PhonologicalRuleCollection
from flexicon.code.Grammar.PhonologicalRule import PhonologicalRule


class PhonologicalRuleOperations(BaseOperations):
    """Operations on phonological rules."""

    def GetAll(self):
        """
        Get all phonological rules as a smart collection.

        Returns:
            PhonologicalRuleCollection: All rules with type breakdown visible.
        """
        raw_rules = self._factory.GetAll()
        wrapped_rules = [PhonologicalRule(rule) for rule in raw_rules]
        return PhonologicalRuleCollection(wrapped_rules)
```

### Example 2: Iterating and Displaying

```python
rules = phonRuleOps.GetAll()

# Display type breakdown
print(rules)
# Output:
# PhonologicalRuleCollection (12 total)
#   PhRegularRule: 7 (58%)
#   PhMetathesisRule: 3 (25%)
#   PhReduplicationRule: 2 (17%)

# Iterate and access properties
for rule in rules:
    print(f"{rule.Name}: {rule.class_type}")
    # All property access is transparent thanks to wrapper

# Access by index
first_rule = rules[0]
print(first_rule.Name)
```

### Example 3: Type Filtering

```python
rules = phonRuleOps.GetAll()

# Get rules of specific type
regular_rules = rules.by_type('PhRegularRule')
print(f"Regular rules: {len(regular_rules)}")  # 7

# Use convenience method
just_regular = rules.regular_rules()
print(f"Regular rules: {len(just_regular)}")  # Same as above

# Check what types exist
if rules.has_type('PhMetathesisRule'):
    metathesis = rules.by_type('PhMetathesisRule')
    print(f"Found {len(metathesis)} metathesis rules")

# Get type counts
counts = rules.by_type_count()
for class_type, count in counts.items():
    print(f"{class_type}: {count}")
```

### Example 4: Custom Filtering

```python
rules = phonRuleOps.GetAll()

# Filter by name
voicing_rules = rules.filter(name_contains='voicing')
print(voicing_rules)
# Output shows only rules matching the filter

# Filter by direction
ltr_rules = rules.filter(direction='LTR')
print(ltr_rules)

# Combine filters (both name AND direction match)
ltr_voicing = rules.filter(name_contains='voicing', direction='LTR')

# Chain filters (filter by type, then by name)
regular_voicing = rules.by_type('PhRegularRule').filter(name_contains='voicing')
print(regular_voicing)
# Output:
# PhonologicalRuleCollection (2 total)
#   PhRegularRule: 2 (100%)
```

### Example 5: Slicing

```python
rules = phonRuleOps.GetAll()

# Get first 3 rules
first_three = rules[0:3]
print(type(first_three))  # PhonologicalRuleCollection
print(first_three)  # Shows type breakdown of the 3 rules

# Get specific rule
first = rules[0]
print(type(first))  # PhonologicalRule (single object)

# Get every other rule
every_other = rules[::2]
print(len(every_other))  # ~6 rules
print(every_other)  # Type breakdown of filtered set
```

### Example 6: Building a Collection Manually

```python
from flexicon.code.Grammar.phonological_rule_collection import PhonologicalRuleCollection

# Create empty collection
collection = PhonologicalRuleCollection()

# Add items
collection.append(rule1)
collection.extend([rule2, rule3, rule4])

# Or create with items
rules = PhonologicalRuleCollection([rule1, rule2, rule3])

print(rules)  # Shows type breakdown
```

---

## Benefits of Smart Collections

### 1. Type Visibility
Users immediately see what types are in the collection:

```python
print(rules)  # Shows breakdown without asking "what types are here?"
```

### 2. Easy Type Filtering
No manual iteration and checking:

```python
# Simple
regular = rules.by_type('PhRegularRule')

# vs. complex
regular = [r for r in rules if r.ClassName == 'PhRegularRule']
```

### 3. Domain-Specific Filtering
Collections provide natural methods for their domain:

```python
# Natural to the domain
voicing = rules.filter(name_contains='voicing')

# vs. generic
voicing = [r for r in rules if 'voicing' in r.Name]
```

### 4. Unified Interface Across Types
Users work with mixed types naturally:

```python
# Works on all rule types uniformly
for rule in rules:
    process(rule)  # Wrappers handle type-specific behavior
```

### 5. Better Error Messages
When filtering finds nothing:

```python
empty = rules.filter(name_contains='nonexistent')
print(empty)
# Output: PhonologicalRuleCollection (empty)
# Clear indication that filter ran but found nothing
```

---

## Advanced Patterns

### Pattern: Collection with Additional Methods

Add domain-specific analysis methods:

```python
class PhonologicalRuleCollection(SmartCollection):
    """Collection with analysis methods."""

    def get_by_output_count(self):
        """
        Group rules by number of output specs.

        Returns:
            dict: Mapping of output_count -> RuleCollection
        """
        groups = {}
        for rule in self._items:
            if rule.has_output_specs:
                count = rule.RightHandSidesOS.Count
                if count not in groups:
                    groups[count] = []
                groups[count].append(rule)

        return {
            count: PhonologicalRuleCollection(items)
            for count, items in groups.items()
        }

    def get_complexity_stats(self):
        """
        Get statistics about rule complexity.

        Returns:
            dict: Stats like avg_input_contexts, max_inputs, etc.
        """
        if not self._items:
            return {'count': 0}

        input_counts = [
            rule.input_context_count
            for rule in self._items
        ]

        return {
            'total': len(self._items),
            'avg_inputs': sum(input_counts) / len(input_counts),
            'max_inputs': max(input_counts),
            'min_inputs': min(input_counts),
        }
```

### Pattern: Caching in Collections

For expensive operations, cache results:

```python
class OptimizedCollection(SmartCollection):
    """Collection with caching for expensive operations."""

    def __init__(self, items=None):
        super().__init__(items)
        self._filter_cache = {}

    def filter(self, **criteria):
        """Filter with caching."""
        # Create cache key from criteria
        cache_key = tuple(sorted(criteria.items()))

        if cache_key in self._filter_cache:
            return self._filter_cache[cache_key]

        # Perform filtering
        filtered = self._items[:]
        # ... filter logic ...

        result = type(self)(filtered)
        self._filter_cache[cache_key] = result
        return result

    def clear_filter_cache(self):
        """Clear the filter cache (call when items change)."""
        self._filter_cache.clear()
```

---

## When to Create Collection Subclasses

Create a collection subclass when:

1. **Multiple concrete types in collection**
   - Phonological rules (Regular, Metathesis, Reduplication)
   - MSA types (Stem, DerivAff, InflAff, UnclassifiedAff)

2. **Domain-specific filtering patterns**
   - Rules: filter by name, direction, output count
   - Entries: filter by gloss, POS, morph type

3. **Collection-level analysis**
   - Type breakdown by count
   - Statistics about the collection
   - Grouping items by properties

4. **Convenience methods for common patterns**
   - `regular_rules()` instead of `by_type('PhRegularRule')`
   - `by_pos()` to group entries

### When NOT to Create a Collection

Don't create collections for:
- **Single operation results** that won't be reused
- **Simple lists** that don't need filtering
- **Small collections** (< 10 items) that won't benefit from smart display

---

## Subclassing Pattern

When creating a collection for a new domain:

```python
from flexicon.code.Shared.smart_collection import SmartCollection


class DomainObjectCollection(SmartCollection):
    """
    Collection of domain-specific objects with type-aware display and filtering.

    If objects have multiple concrete types, SmartCollection automatically
    shows the breakdown. Custom filter() provides domain-specific filtering.
    """

    def __init__(self, items=None):
        """Initialize with domain objects."""
        super().__init__(items)

    def filter(self, **criteria):
        """
        Filter using domain-specific criteria.

        Args:
            **criteria: Domain-specific parameters.

        Returns:
            DomainObjectCollection: New collection with filtered items.
        """
        filtered = self._items[:]

        # Domain-specific filtering logic here
        # ...

        return DomainObjectCollection(filtered)

    # Add domain-specific convenience methods
    def get_by_property(self):
        """Group items by some property."""
        # Implementation here
        pass
```

---

## See Also

- `flexicon/code/Shared/smart_collection.py` - SmartCollection base class
- `docs/ARCHITECTURE_WRAPPERS.md` - Wrapper classes (often used with collections)
- `CLAUDE.md` - Design philosophy and conventions
