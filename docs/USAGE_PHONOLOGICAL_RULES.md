# Using Phonological Rules in Flexicon

This guide shows how to work with phonological rules in Flexicon, including the new wrapper classes that simplify access to rules without exposing ClassName or casting complexity.

## Overview

Phonological rules in FieldWorks come in three concrete types:
- **PhRegularRule**: Standard phonological rules with output specifications
- **PhMetathesisRule**: Metathesis rules that swap segments
- **PhReduplicationRule**: Reduplication rules that repeat segments

All three types share common properties (name, direction, input contexts) but have type-specific properties.

Flexicon provides a unified interface through the `PhonologicalRule` wrapper class, which transparently handles these differences so you don't need to check `ClassName` or cast objects manually.

## Before: The Old Way

Without wrappers, you had to deal with casting and type checking:

```python
from flexicon import FLExProject, PhonologicalRuleOperations

project = FLExProject()
project.OpenProject("my project")

phonRuleOps = PhonologicalRuleOperations(project)

# Get all rules - generator that yields raw objects
for rule in phonRuleOps.GetAll():
    # Get name using operation method
    name = phonRuleOps.GetName(rule)
    print(f"Rule: {name}")

    # Check type to access type-specific properties
    if rule.ClassName == 'PhRegularRule':
        # Need to cast to access RightHandSidesOS
        from flexicon.code.lcm_casting import cast_to_concrete
        concrete = cast_to_concrete(rule)
        for rhs in concrete.RightHandSidesOS:
            print(f"Output: {rhs}")
    elif rule.ClassName == 'PhMetathesisRule':
        concrete = cast_to_concrete(rule)
        for part in concrete.LeftPartOfMetathesisOS:
            print(f"Left part: {part}")

project.CloseProject()
```

## After: The New Wrapper Way

With wrappers, you access properties directly without casting:

```python
from flexicon import FLExProject, PhonologicalRuleOperations

project = FLExProject()
project.OpenProject("my project")

phonRuleOps = PhonologicalRuleOperations(project)

# Get all rules - returns RuleCollection of wrapped objects
rules = phonRuleOps.GetAll()

# Print collection shows type breakdown
print(rules)
# RuleCollection (12 total)
#   PhRegularRule: 7 (58%)
#   PhMetathesisRule: 3 (25%)
#   PhReduplicationRule: 2 (17%)

# Access properties directly on wrapped rules
for rule in rules:
    print(f"Rule: {rule.name}")  # No GetName() needed

    # Check capability with clear property names
    if rule.has_output_specs:
        for spec in rule.output_specs:
            print(f"Output: {spec}")

    # Different capability check for metathesis
    if rule.has_metathesis_parts:
        left, right = rule.metathesis_parts
        print(f"Metathesis: {left} <-> {right}")

project.CloseProject()
```

## Common Patterns

### Accessing Rule Properties

All rules have these common properties:

```python
rules = phonRuleOps.GetAll()

for rule in rules:
    print(rule.name)           # Rule name (string)
    print(rule.direction)      # 0=LTR, 1=RTL, 2=simultaneous
    print(rule.stratum)        # IMoStratum object or None
    print(rule.input_contexts) # List of input contexts (StrucDescOS)
```

### Checking Type Capabilities

Instead of checking `ClassName`, use capability check properties:

```python
# Check if rule has output specifications (PhRegularRule only)
if rule.has_output_specs:
    for spec in rule.output_specs:
        # Process output specifications
        pass

# Check if rule is a metathesis rule
if rule.has_metathesis_parts:
    left_parts, right_parts = rule.metathesis_parts
    # Process metathesis parts

# Check if rule is a reduplication rule
if rule.has_redup_parts:
    left_parts, right_parts = rule.redup_parts
    # Process reduplication parts
```

### Filtering Rules

The `RuleCollection` provides multiple ways to filter:

```python
rules = phonRuleOps.GetAll()

# Filter to specific type
regular_rules = rules.regular_rules()
metathesis_rules = rules.metathesis_rules()
redup_rules = rules.redup_rules()

# Filter by name (case-sensitive)
voicing_rules = rules.filter(name_contains='voicing')

# Filter by direction
ltr_rules = rules.filter(direction=0)  # Left-to-right
rtl_rules = rules.filter(direction=1)  # Right-to-left

# Custom filtering with where()
complex_rules = rules.where(lambda r: len(r.input_contexts) > 2)

# Chain filters
voicing_regular = rules.regular_rules().filter(name_contains='voicing')
voicing_ltr_regular = (
    rules.regular_rules()
        .filter(name_contains='voicing')
        .filter(direction=0)
)
```

### Creating and Finding Rules

Rules are still created and found using operation methods, but Find() now returns wrapped objects:

```python
# Create new rule
rule = phonRuleOps.Create("New Rule")

# Find rule by name (case-insensitive search)
found = phonRuleOps.Find("Voicing Assimilation")
if found:
    print(f"Found: {found.name}")

# Modify through operations
phonRuleOps.SetName(found, "Modified Name")
```

### Accessing Raw C# Interfaces (Advanced)

For users who need direct access to C# interfaces for advanced operations:

```python
rule = rules[0]

# For regular rules
if regular_rule := rule.as_regular_rule():
    # Access IPhRegularRule interface directly
    rhs_count = regular_rule.RightHandSidesOS.Count
    # Advanced C# operations...

# For metathesis rules
if metathesis_rule := rule.as_metathesis_rule():
    # Access IPhMetathesisRule interface directly
    # Advanced C# operations...

# For reduplication rules
if redup_rule := rule.as_reduplication_rule():
    # Access IPhReduplicationRule interface directly
    # Advanced C# operations...

# Or access raw concrete directly
concrete = rule.concrete
# Concrete is the appropriate interface for the rule's type
```

## Backward Compatibility

The wrapper is backward compatible with existing code:

```python
# Old code that expects to call GetName()
found = phonRuleOps.Find("Some Rule")
if found:
    # This still works - wrapped rule has _obj attribute
    # with the original LCM object inside
    name = phonRuleOps.GetName(found)  # Works!
    # Though rule.name is simpler

# Wrapped rules also pass through attribute access
# to the underlying LCM object
rule = rules[0]
# Properties on underlying object are accessible:
rule.ClassName  # Still works (via __getattr__)
```

## Integration with Operations

While wrappers simplify property access, operations methods remain the primary way to modify rules:

```python
rules = phonRuleOps.GetAll()

# Access wrapped rule
rule = rules[0]

# Use operation methods for modifications
phonRuleOps.SetName(rule, "New Name")
phonRuleOps.SetDirection(rule, 1)

# Or through wrapper properties (if implemented)
# Note: Setters are not part of the wrapper
# Use operation methods for all modifications

# Duplicate a rule
duplicate = phonRuleOps.Duplicate(rule)
wrapped_duplicate = phonRuleOps.Find(phonRuleOps.GetName(duplicate))
```

## Performance Considerations

- `RuleCollection` wraps all rules, so large collections have minimal overhead
- Filtering creates new collections (no in-place modification)
- All filtering is O(n) where n is collection size
- Wrapping objects is very lightweight

## Common Questions

### Why doesn't my rule have RightHandSidesOS?

Check if it's actually a PhRegularRule:

```python
if rule.has_output_specs:
    # Safe to use rule.output_specs
    pass
else:
    # This rule doesn't have output specifications
    # It might be metathesis or reduplication
    if rule.has_metathesis_parts:
        print("This is a metathesis rule")
```

### How do I know what type of rule it is?

```python
rule = rules[0]

print(rule.class_type)  # 'PhRegularRule', 'PhMetathesisRule', or 'PhReduplicationRule'

# Or use capability checks
if rule.has_output_specs:
    print("This is a PhRegularRule")
elif rule.has_metathesis_parts:
    print("This is a PhMetathesisRule")
elif rule.has_redup_parts:
    print("This is a PhReduplicationRule")
```

### Can I still use operation methods with wrapped rules?

Yes, wrapped rules are fully compatible with operation methods:

```python
rule = phonRuleOps.Find("Some Rule")
phonRuleOps.SetName(rule, "New Name")  # Works - passes wrapped object
phonRuleOps.GetDescription(rule)       # Works
phonRuleOps.Delete(rule)               # Works
```

### What about attributes that aren't exposed by the wrapper?

Use the wrapper's property access:

```python
rule = rules[0]

# Wrapper properties
print(rule.name)
print(rule.direction)

# Attributes on underlying object (via __getattr__)
print(rule.Hvo)  # HVO of the rule
print(rule.Guid) # GUID of the rule

# For advanced users: direct concrete access
if regular := rule.as_regular_rule():
    # Access any property on IPhRegularRule
    print(regular.SomeProperty)
```

## See Also

- `PhonologicalRule` - The wrapper class documentation
- `RuleCollection` - The smart collection class documentation
- `PhonologicalRuleOperations` - The operations class documentation
