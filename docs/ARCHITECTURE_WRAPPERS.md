# Wrapper Classes Architecture Guide

## Overview

Wrapper classes are a fundamental pattern in Flexicon for solving the two-layer LCM type system problem. They provide a transparent, user-friendly interface that hides the complexity of pythonnet casting while maximizing the functionality of LCM objects.

This guide explains why wrapper classes exist, how they work, and how to create new ones for your domain.

---

## The Problem: Two-Layer LCM Type System

### How LCM Works in pythonnet

FieldWorks Language Explorer (FLEx) uses the Language and Culture Model (LCM) API, which is built on .NET. When you access objects in pythonnet, you encounter a two-layer type system:

1. **Base Interface** (e.g., `IPhSegmentRule`, `IMoMorphSynAnalysis`)
   - Generic interface that all objects of a type implement
   - What pythonnet returns from collections
   - Has common properties shared across all concrete types

2. **Concrete Type** (identified by `ClassName` attribute)
   - The actual runtime class (e.g., "PhRegularRule", "MoStemMsa")
   - Determines which concrete interface has additional properties
   - The ONLY way to know the real type in Python

3. **Concrete Interface** (e.g., `IPhRegularRule`, `IMoStemMsa`)
   - Type-specific interface with additional properties
   - Must be explicitly cast to from the base interface
   - Not accessible without casting

### The Casting Problem

Consider getting phonological rules:

```python
# Without wrapping - what users would have to do:
from SIL.LCModel import IPhRegularRule, IPhMetathesisRule

rules = phonRuleOps.GetAll()  # Returns IPhSegmentRule objects

for rule in rules:
    # Access common property (works)
    print(rule.Name)

    # Try to access type-specific property (FAILS!)
    if rule.ClassName == 'PhRegularRule':
        # Python won't let us access this without casting
        # because rule is still typed as IPhSegmentRule
        print(rule.RightHandSidesOS)  # AttributeError!

    # What users would have to do (tedious!)
    if rule.ClassName == 'PhRegularRule':
        concrete = IPhRegularRule(rule)  # Manual cast required
        print(concrete.RightHandSidesOS)  # Now it works
    elif rule.ClassName == 'PhMetathesisRule':
        concrete = IPhMetathesisRule(rule)  # Different cast needed
        print(concrete.LeftPartOfMetathesisOS)
```

This is error-prone and clutters user code.

---

## The Solution: Wrapper Classes

Wrapper classes store both the base interface and the concrete type, then use `__getattr__()` to intelligently route property access.

### How Wrappers Solve the Problem

```python
# With wrapping - what users experience:
from flexicon.code.Grammar.PhonologicalRuleOperations import PhonologicalRuleOperations

rules = phonRuleOps.GetAll()  # Returns wrapped objects

for rule in rules:
    # Access common property (works)
    print(rule.Name)

    # Access type-specific property (WORKS WITHOUT CASTING!)
    if rule.class_type == 'PhRegularRule':
        # Wrapper transparently casts and accesses
        print(rule.RightHandSidesOS)  # Just works!
    elif rule.class_type == 'PhMetathesisRule':
        # Different concrete type, same seamless access
        print(rule.LeftPartOfMetathesisOS)

    # Or use capability checks instead of type checking
    if rule.has_output_specs:
        print(rule.RightHandSidesOS)
```

Much cleaner! The wrapper handles all the casting internally.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User Code (What They Actually Write)                        │
│                                                               │
│  rule = GetAll()[0]                                           │
│  print(rule.Name)              # Common property              │
│  print(rule.RightHandSidesOS)  # Type-specific property      │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼ (Transparent routing)
┌─────────────────────────────────────────────────────────────┐
│  Wrapper Class (PhonologicalRule)                            │
│                                                               │
│  - Stores _obj (base interface)                               │
│  - Stores _concrete (concrete interface)                      │
│  - __getattr__() routes property access                       │
│  - class_type property for type checking                      │
│  - Smart properties for capability checks                     │
└──────────────┬──────────────────────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼              ▼
┌──────────────┐  ┌──────────────┐
│ Base Type    │  │ Concrete     │
│ IPhSegment   │  │ IPhRegularRule
│ Rule         │  │ IPhMetathesis
│              │  │ IPhReduplication
│ Common:      │  │
│ - Name       │  │ Type-Specific:
│ - StrucDescOS│  │ - RightHandSidesOS
└──────────────┘  │ - LeftPartOfMetathesis
                  │ - LeftPartOfReduplication
                  └──────────────┘
```

---

## Wrapper Class Pattern

### Base Wrapper: LCMObjectWrapper

Flexicon provides `LCMObjectWrapper` as the base class for all wrappers:

```python
from flexicon.code.Shared.wrapper_base import LCMObjectWrapper

class PhonologicalRule(LCMObjectWrapper):
    """
    Wrapper around IPhSegmentRule for unified property access.

    Transparently handles casting to concrete types (PhRegularRule,
    PhMetathesisRule, PhReduplicationRule).
    """

    def __init__(self, lcm_obj):
        """Initialize with an IPhSegmentRule object."""
        super().__init__(lcm_obj)
```

### Key Properties and Methods

#### 1. class_type Property

Get the concrete type as a string:

```python
rule = PhonologicalRule(lcm_rule)

if rule.class_type == 'PhRegularRule':
    # This is a regular rule
    pass
elif rule.class_type == 'PhMetathesisRule':
    # This is a metathesis rule
    pass

# Use in collections
print(f"Rule type: {rule.class_type}")
```

#### 2. get_property() Method

Safely access properties with a default fallback:

```python
# Safe access to optional properties
output_specs = rule.get_property('RightHandSidesOS')
if output_specs:
    print(f"Rule has {output_specs.Count} output specs")

# Provide meaningful defaults
context_count = rule.get_property('StrucDescOS', [])
print(f"Input contexts: {len(context_count)}")

# Works for any type
frequency = rule.get_property('Frequency', 0)
```

#### 3. Direct Property Access

The wrapper routes property access transparently:

```python
rule = PhonologicalRule(lcm_rule)

# Common properties (on base interface)
print(rule.Name)           # Works directly
print(rule.ClassName)      # Works directly

# Type-specific properties (on concrete interface)
# No casting needed - wrapper handles it!
if rule.class_type == 'PhRegularRule':
    output = rule.RightHandSidesOS  # Just works!

# Wrapper tries concrete first, then base interface
# So mixed access patterns work smoothly
```

---

## Creating Domain-Specific Wrappers

### Pattern: Phonological Rules Wrapper

Here's a complete example of a domain-specific wrapper:

```python
from flexicon.code.Shared.wrapper_base import LCMObjectWrapper


class PhonologicalRule(LCMObjectWrapper):
    """
    Wrapper for IPhSegmentRule providing unified interface across all
    phonological rule types (Regular, Metathesis, Reduplication).

    Transparently handles type-specific properties and provides
    convenience properties that work across all types.
    """

    # Type constants for convenience
    REGULAR = 'PhRegularRule'
    METATHESIS = 'PhMetathesisRule'
    REDUPLICATION = 'PhReduplicationRule'

    def __init__(self, lcm_obj):
        """
        Initialize wrapper with an IPhSegmentRule object.

        Args:
            lcm_obj: An IPhSegmentRule object (from LCM).
        """
        super().__init__(lcm_obj)

    # ========== Type Capability Checks ==========
    # These allow checking "what can this rule do?" instead of "what type is it?"

    @property
    def is_regular_rule(self):
        """Check if this is a regular phonological rule."""
        return self.class_type == self.REGULAR

    @property
    def is_metathesis_rule(self):
        """Check if this is a metathesis rule."""
        return self.class_type == self.METATHESIS

    @property
    def is_reduplication_rule(self):
        """Check if this is a reduplication rule."""
        return self.class_type == self.REDUPLICATION

    @property
    def has_output_specs(self):
        """Check if rule has output specifications (Regular rules only)."""
        return self.get_property('RightHandSidesOS') is not None

    @property
    def has_metathesis_parts(self):
        """Check if rule has metathesis parts (Metathesis rules only)."""
        return self.get_property('LeftPartOfMetathesisOS') is not None

    @property
    def has_reduplication_parts(self):
        """Check if rule has reduplication parts (Reduplication rules only)."""
        return self.get_property('LeftPartOfReduplicationOS') is not None

    # ========== Convenience Properties ==========
    # These provide common functionality across all types

    @property
    def input_contexts(self):
        """
        Get the input contexts (structural descriptions).

        Available on all phonological rule types.
        """
        contexts = self.get_property('StrucDescOS', [])
        return list(contexts) if contexts else []

    @property
    def input_context_count(self):
        """Get the number of input contexts."""
        return len(self.input_contexts)

    # ========== Type-Specific Properties (via __getattr__) ==========
    # These are automatically routed by the wrapper:
    #
    # Regular rules:
    #   - rule.RightHandSidesOS
    #
    # Metathesis rules:
    #   - rule.LeftPartOfMetathesisOS
    #   - rule.RightPartOfMetathesisOS
    #
    # Reduplication rules:
    #   - rule.LeftPartOfReduplicationOS
    #   - rule.RightPartOfReduplicationOS


# Usage example in operations class
class PhonologicalRuleOperations(BaseOperations):
    """Operations on phonological rules."""

    def GetAll(self):
        """Get all phonological rules wrapped."""
        raw_rules = factory.GetAll()
        # Wrap each rule for transparent property access
        wrapped = [PhonologicalRule(rule) for rule in raw_rules]
        return RuleCollection(wrapped)
```

### Pattern: Morphosyntactic Analysis (MSA) Wrapper

Another example with multiple concrete types:

```python
from flexicon.code.Shared.wrapper_base import LCMObjectWrapper


class MorphoSyntacticAnalysis(LCMObjectWrapper):
    """
    Wrapper for IMoMorphSynAnalysis providing unified interface across all
    MSA types (Stem, DerivAff, InflAff, UnclassifiedAff).
    """

    # Type constants
    STEM = 'MoStemMsa'
    DERIV_AFF = 'MoDerivAffMsa'
    INFL_AFF = 'MoInflAffMsa'
    UNCLASSIFIED_AFF = 'MoUnclassifiedAffixMsa'

    @property
    def msa_type(self):
        """Get the specific MSA type."""
        return self.class_type

    @property
    def is_stem_msa(self):
        """Is this a stem MSA?"""
        return self.class_type == self.STEM

    @property
    def is_affix_msa(self):
        """Is this an affix MSA of any kind?"""
        affix_types = {self.DERIV_AFF, self.INFL_AFF, self.UNCLASSIFIED_AFF}
        return self.class_type in affix_types

    @property
    def part_of_speech(self):
        """
        Get the part of speech (available on Stem and InflAff MSAs).

        Returns:
            IPartOfSpeech or None if not available on this MSA type.
        """
        return self.get_property('PartOfSpeechRA')

    @property
    def pos_name(self):
        """Get the part of speech name (if available)."""
        pos = self.part_of_speech
        if pos:
            return pos.Name.BestAnalysisAlternative.Text
        return None
```

---

## Smart Properties and Capability Checks

Instead of forcing users to check `ClassName` and understand type-specific properties, use capability checks:

### Bad Pattern (Type Checking)

```python
# This is what we want to avoid:
for rule in rules:
    if rule.ClassName == 'PhRegularRule':
        from SIL.LCModel import IPhRegularRule
        concrete = IPhRegularRule(rule)
        output = concrete.RightHandSidesOS
    # ... more if/elif blocks for other types
```

### Good Pattern (Capability Checking)

```python
# This is what the wrapper enables:
for rule in rules:
    # Check what the rule CAN DO, not what type it IS
    if rule.has_output_specs:
        output = rule.RightHandSidesOS  # Transparent access

    if rule.has_metathesis_parts:
        left = rule.LeftPartOfMetathesisOS

    if rule.has_reduplication_parts:
        left = rule.LeftPartOfReduplicationOS
```

The second approach is:
- **User-friendly:** Describes what the object can do
- **Type-safe:** No casting boilerplate
- **Extensible:** Add new capability checks without changing user code

---

## Code Examples

### Example 1: Creating a Wrapper

```python
from flexicon.code.Shared.wrapper_base import LCMObjectWrapper
from SIL.LCModel import IPhSegmentRule  # Type annotation only


def get_phonological_rule(rule_hvo: int) -> PhonologicalRule:
    """
    Get a phonological rule and wrap it.

    Args:
        rule_hvo: HVO (handle to object) of the rule.

    Returns:
        PhonologicalRule: Wrapped rule object.
    """
    raw_rule = project.Services.GetObject(rule_hvo)  # IPhSegmentRule
    return PhonologicalRule(raw_rule)
```

### Example 2: Accessing Properties Through Wrapper

```python
from flexicon.code.Grammar.PhonologicalRuleOperations import PhonologicalRuleOperations

ops = project.PhonologicalRules

# Get all rules (returns wrapped objects)
rules = ops.GetAll()

for rule in rules:
    # Common properties work on all types
    print(f"Name: {rule.Name}")
    print(f"Type: {rule.class_type}")

    # Type-specific properties accessed transparently
    if rule.is_regular_rule:
        print(f"  Output specs: {len(rule.RightHandSidesOS)}")

    # Or use capability checks (preferred)
    if rule.has_output_specs:
        print(f"  Outputs: {rule.RightHandSidesOS.Count}")
```

### Example 3: Using class_type Property

```python
rules = ops.GetAll()

# Type checking the right way
regular_rules = [r for r in rules if r.class_type == 'PhRegularRule']
metathesis_rules = [r for r in rules if r.class_type == 'PhMetathesisRule']

# But smart collections make this easier (see ARCHITECTURE_COLLECTIONS.md)
```

### Example 4: Using get_property() with Defaults

```python
rule = PhonologicalRule(lcm_rule)

# Safe access with fallback
output_count = len(rule.get_property('RightHandSidesOS', []))
context_count = len(rule.get_property('StrucDescOS', []))

print(f"Rule has {context_count} contexts and {output_count} outputs")
# Works even if properties don't exist - returns defaults
```

---

## Benefits of Wrapper Classes

### 1. No Casting Boilerplate
Users never write `IPhRegularRule(obj)` - the wrapper handles it.

### 2. IDE Autocomplete Support
IDEs can understand wrapper properties:
```python
rule = PhonologicalRule(obj)
rule.  # IDE suggests properties even across concrete types
```

### 3. Unified Interface
All rules behave the same way regardless of concrete type.

### 4. Better Error Messages
```python
# Without wrapper:
AttributeError: 'IPhSegmentRule' object has no attribute 'RightHandSidesOS'

# With wrapper:
AttributeError: 'PhonologicalRule' object and its wrapped LCM object
               have no attribute 'NonExistentProperty'
```

### 5. Clear Intent
```python
# What does this do?
if rule.has_output_specs:  # Clear! Check if outputs exist
    process_outputs()

# vs.

if rule.ClassName == 'PhRegularRule':  # Vague coupling to implementation
    process_outputs()
```

---

## Performance Considerations

### Minimal Overhead

Wrapper overhead is negligible:
- `__init__()`: One call to `cast_to_concrete()` (cached by pythonnet)
- `__getattr__()`: Two `getattr()` calls (attribute lookup, not computation)
- Properties: Computed on demand (no initialization cost)

### Lazy Evaluation

Concrete type is only cast when needed:

```python
rule = PhonologicalRule(obj)

# Accessing common properties - minimal overhead
print(rule.Name)  # Directly on base interface

# Accessing type-specific properties - automatic cast
print(rule.RightHandSidesOS)  # Routed to concrete interface
```

### No Collection Overhead

Wrapping in collections is cheap:

```python
# Just wrapping objects, not cloning them
wrapped = [PhonologicalRule(obj) for obj in raw_objects]
# ~0.1ms per object on modern hardware
```

---

## When to Create Wrapper Subclasses

Create a wrapper subclass when you have:

1. **Multiple concrete types implementing the same base interface**
   - Phonological rules (Regular, Metathesis, Reduplication)
   - MSA types (Stem, DerivAff, InflAff, UnclassifiedAff)
   - Contexts (various context types)

2. **Type-specific properties that users need to access**
   - Different types have different properties
   - Want to hide the `ClassName` checking logic

3. **Capability checks that vary by type**
   - "Does this rule have output specs?" (Regular only)
   - "Does this MSA have a POS?" (Stem and InflAff only)

4. **Common convenience properties across types**
   - Input contexts (all phonological rules have these)
   - POS name (multiple MSA types have POS)

### When NOT to Create a Wrapper

Don't create wrappers for:
- **Single concrete types** (only one implementation)
  - E.g., ILexEntry, ILexSense (no subtypes)
  - Use direct LCM objects or simple operation methods

- **Simple data objects with no type hierarchy**
  - Use direct property access instead

- **Temporary/internal objects**
  - Only wrap when exposing to users

---

## Subclassing Pattern

When creating a wrapper for a new domain:

```python
from flexicon.code.Shared.wrapper_base import LCMObjectWrapper


class DomainSpecificObject(LCMObjectWrapper):
    """
    Wrapper for IDomainBase providing unified access to concrete types.

    Concrete types:
    - DomainType1: Special property X
    - DomainType2: Special property Y
    - DomainType3: Special property Z
    """

    # Type constants for easy reference
    TYPE1 = 'DomainType1'
    TYPE2 = 'DomainType2'
    TYPE3 = 'DomainType3'

    def __init__(self, lcm_obj):
        """Initialize wrapper with a domain object."""
        super().__init__(lcm_obj)

    # Type checking properties
    @property
    def is_type1(self):
        """Check if this is Type1."""
        return self.class_type == self.TYPE1

    # Capability checks
    @property
    def has_special_property_x(self):
        """Check if this type has special property X."""
        return self.get_property('SpecialPropertyX') is not None

    # Convenience properties
    @property
    def special_name(self):
        """Get a special computed property."""
        prop = self.get_property('SpecialPropertyX')
        return prop.Name if prop else "Unknown"
```

---

## See Also

- `flexicon/code/Shared/wrapper_base.py` - Base wrapper implementation
- `flexicon/code/lcm_casting.py` - Casting utilities used internally
- `docs/ARCHITECTURE_COLLECTIONS.md` - Smart collections (often used with wrappers)
- `CLAUDE.md` - Design philosophy and conventions
