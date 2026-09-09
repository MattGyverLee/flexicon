# Flexicon Architecture Overview

## Introduction

Flexicon is built on a foundation of patterns and principles designed to make accessing FieldWorks Language Explorer (FLEx) data safe, intuitive, and powerful. This document provides a high-level overview of the architecture and guides you to detailed documentation for each component.

---

## Core Architecture: Wrapper + Collection Pattern

The heart of Flexicon v2.2+ architecture is a two-part pattern that solves the complexity of the underlying LCM (Language and Culture Model) API:

### 1. Wrapper Classes

**Problem:** LCM uses a two-layer type system where objects are typed as base interfaces but have concrete type-specific properties accessible only through casting.

**Solution:** Wrapper classes store both the base interface and concrete type, providing transparent property access without user-visible casting.

**Key Benefits:**
- No casting boilerplate for users
- IDE autocomplete support
- Clear capability checks instead of type checking
- Better error messages

**See:** `docs/ARCHITECTURE_WRAPPERS.md` for comprehensive documentation

**Example:**
```python
# User experience with wrappers:
rules = phonRuleOps.GetAll()
for rule in rules:
    # Access type-specific properties transparently
    if rule.has_output_specs:
        print(rule.RightHandSidesOS)  # Just works!
```

### 2. Smart Collections

**Problem:** Collections of objects with multiple concrete types need to show type diversity while still supporting unified operations.

**Solution:** SmartCollection provides type-aware display, type filtering, and domain-specific filter methods.

**Key Benefits:**
- Type breakdown visible on display
- Easy type filtering with `by_type()`
- Domain-specific filtering with `filter()`
- Standard Python collection interface

**See:** `docs/ARCHITECTURE_COLLECTIONS.md` for comprehensive documentation

**Example:**
```python
# User experience with smart collections:
rules = phonRuleOps.GetAll()
print(rules)  # Shows type breakdown
# Output:
# PhonologicalRuleCollection (12 total)
#   PhRegularRule: 7 (58%)
#   PhMetathesisRule: 3 (25%)

voicing = rules.filter(name_contains='voicing')  # Domain-specific filter
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  User Code (High-Level, Natural Interface)              │
│                                                           │
│  rules = phonRuleOps.GetAll()                            │
│  for rule in rules:                                       │
│      print(rule.has_output_specs)  # Works transparently│
└──────────────┬──────────────────────────────────────────┘
               │
               ├─────────────────────┬────────────────────┐
               ▼                     ▼                    ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐
    │  Smart          │  │  Wrapped Items   │  │  Operations  │
    │  Collections    │  │ (Wrappers)       │  │  Classes     │
    │                 │  │                  │  │              │
    │  - Type display │  │ - Transparent    │  │ - GetAll()   │
    │  - Filtering    │  │   property access│  │ - Get()      │
    │  - Domain       │  │ - Capability     │  │ - Create()   │
    │    specific     │  │   checks         │  │ - Update()   │
    └──────┬──────────┘  └──────┬───────────┘  │ - Delete()   │
           │                    │              └──────┬───────┘
           └────────┬───────────┘                     │
                    ▼                                 │
    ┌──────────────────────────────────┐             │
    │  LCM Casting Layer               │             │
    │  (lcm_casting.py)                │◄────────────┘
    │                                   │
    │  - cast_to_concrete()             │
    │  - validate_merge_compatibility()│
    │  - clone_properties()             │
    └──────────────┬────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  LCM Objects (pythonnet)          │
    │  from SIL.LCModel                 │
    │                                   │
    │  - Base interfaces (IPhSegmentRule)
    │  - Concrete types (PhRegularRule) │
    │  - Direct property access        │
    └──────────────────────────────────┘
```

---

## Component Details

### Wrapper Classes

**Files:**
- `flexicon/code/Shared/wrapper_base.py` - Base wrapper implementation
- Domain-specific wrappers in respective modules

**Responsibility:**
- Transparently handle two-layer LCM type system
- Provide `class_type` property for type checking
- Provide `get_property()` for safe property access
- Route property access intelligently across interfaces

**When to Use:**
- When objects have multiple concrete type implementations
- When type-specific properties need to be accessed
- When you want to hide casting complexity from users

**Reference:** `docs/ARCHITECTURE_WRAPPERS.md`

### Smart Collections

**Files:**
- `flexicon/code/Shared/smart_collection.py` - Base collection class
- Domain-specific collections in respective modules

**Responsibility:**
- Show type breakdown via `__str__()`
- Provide `by_type()` for type filtering
- Provide abstract `filter()` for subclass implementation
- Standard Python collection interface (`__iter__`, `__len__`, `__getitem__`)

**When to Use:**
- When returning collections of mixed types
- When type filtering is needed
- When domain-specific filtering is useful

**Reference:** `docs/ARCHITECTURE_COLLECTIONS.md`

### Operations Classes

**Files:**
- `flexicon/code/[Domain]/[Type]Operations.py`

**Responsibility:**
- Implement CRUD operations (Get, GetAll, Create, Update, Delete)
- Wrap/unwrap objects at boundaries
- Return smart collections for multi-item results
- Validate parameters and raise appropriate exceptions

**Pattern:**
```python
class MyOperations(BaseOperations):
    def GetAll(self):
        """Return all items as smart collection."""
        raw = self._factory.GetAll()
        wrapped = [MyWrapper(item) for item in raw]
        return MyCollection(wrapped)

    def Get(self, identifier):
        """Return single item as wrapper."""
        raw = self._find(identifier)
        return MyWrapper(raw)
```

### LCM Casting Layer

**Files:**
- `flexicon/code/lcm_casting.py`

**Responsibility:**
- `cast_to_concrete()` - Convert base interface to concrete type
- `validate_merge_compatibility()` - Check merge safety
- `clone_properties()` - Deep clone with proper casting
- Interface type caching for performance

**Usage:** Internal only, never exposed to users

---

## Data Flow Examples

### Example 1: Getting All Items

```
User Code
  ↓
phonRuleOps.GetAll()
  ↓
PhonologicalRuleOperations.GetAll()
  ├─ Get raw objects from LCM factory
  ├─ Wrap each in PhonologicalRule wrapper
  └─ Return PhonologicalRuleCollection
    ↓
User receives collection with type breakdown visible
  ├─ Can iterate: for rule in rules
  ├─ Can filter: rules.filter(name_contains='voicing')
  └─ Can type-filter: rules.by_type('PhRegularRule')
```

### Example 2: Accessing Properties

```
User Code
  ↓
rule.RightHandSidesOS  (on wrapper)
  ↓
PhonologicalRule.__getattr__('RightHandSidesOS')
  ├─ Try _concrete first (more specific)
  │   └─ Success for PhRegularRule
  └─ Fall back to _obj if needed
    ↓
User gets the property without casting
```

### Example 3: Type Checking

```
User Code
  ↓
if rule.class_type == 'PhRegularRule'
  ↓
PhonologicalRule.class_type property
  ├─ Returns _obj.ClassName
  └─ User knows exact type
    ↓
User can now safely access type-specific properties
```

---

## Design Principles

### 1. User-Centric API

The API is designed around how users naturally think about objects, not the underlying technology:

```python
# Good: Matches user thinking
if rule.has_output_specs:
    print(rule.outputs)

# Bad: Exposes technology
if rule.ClassName == 'PhRegularRule':
    concrete = IPhRegularRule(rule)
    print(concrete.RightHandSidesOS)
```

### 2. Hide Complexity

Users should never see:
- `IPhSegmentRule`, `IPhRegularRule`, etc. (interface names)
- `ClassName` checks (except for informational purposes)
- Casting logic (pythonnet casting internals)
- FLEx null markers ('***')

### 3. Maximize Functionality

Collections and wrappers should:
- Support type diversity without forcing separate code paths
- Provide convenience methods for common patterns
- Show type information without forcing users to ask for it

### 4. Fail Gracefully

- Warn on type mismatches instead of errors when possible
- Provide sensible defaults via `get_property()`
- Return empty collections instead of None
- Clear error messages identifying the actual problem

### 5. Transparency Over Magic

- Type breakdown shown explicitly on collections
- Property routing visible through capability checks
- No hidden state changes
- Clear what's happening at each step

---

## Version Changes

### v2.2 Architecture Improvements

Phase 1.1-1.2 Foundation (Sprint 1.1-1.2):
- [DONE] LCMObjectWrapper base class created
- [DONE] SmartCollection base class created
- [DONE] lcm_casting utilities refactored

Phase 1.3 Documentation (Sprint 1.3):
- [DONE] ARCHITECTURE_WRAPPERS.md comprehensive guide
- [DONE] ARCHITECTURE_COLLECTIONS.md comprehensive guide
- [DONE] ARCHITECTURE.md (this file) overview and integration
- [DONE] CLAUDE.md updated with references

Phase 2 Implementation (Sprint 2.1+):
- Domain-specific wrappers for all multi-type domains
- Domain-specific collections for filtered access
- Updated operations classes to use wrappers/collections
- User-facing API improvements

### Breaking Changes

v2.2 is designed for forward compatibility:
- Existing code continues to work (raw LCM objects still accessible)
- New code can use wrappers and collections
- Gradual migration path for users

---

## Common Patterns

### Pattern 1: Simple Wrapper for Multi-Type Domain

```python
from flexicon.code.Shared.wrapper_base import LCMObjectWrapper

class DomainObject(LCMObjectWrapper):
    """Wrapper for base interface with multiple concrete types."""

    @property
    def is_type_a(self):
        return self.class_type == 'TypeA'

    @property
    def has_special_property(self):
        return self.get_property('SpecialPropertyName') is not None

    @property
    def special_value(self):
        return self.get_property('SpecialPropertyName', default_value)
```

### Pattern 2: Collection with Domain Filtering

```python
from flexicon.code.Shared.smart_collection import SmartCollection

class DomainCollection(SmartCollection):
    """Collection with domain-specific filtering."""

    def filter(self, property1=None, property2=None, **kwargs):
        """Filter by domain-specific criteria."""
        filtered = self._items[:]
        if property1:
            filtered = [i for i in filtered if i.property1 == property1]
        if property2:
            filtered = [i for i in filtered if i.property2 == property2]
        return DomainCollection(filtered)
```

### Pattern 3: Operations Class Using Both

```python
class DomainOperations(BaseOperations):
    """Operations using wrappers and collections."""

    def GetAll(self):
        """Return all items as smart collection."""
        raw = self._factory.GetAll()
        wrapped = [DomainObject(item) for item in raw]
        return DomainCollection(wrapped)

    def Get(self, identifier):
        """Return single item as wrapper."""
        raw = self._find(identifier)
        return DomainObject(raw)

    def Create(self, **kwargs):
        """Create and return wrapped object."""
        raw = self._factory.Create(**kwargs)
        return DomainObject(raw)
```

---

## File Organization

```
flexicon/code/
├── Shared/
│   ├── wrapper_base.py           # LCMObjectWrapper base class
│   ├── smart_collection.py       # SmartCollection base class
│   └── ...other utilities...
│
├── Grammar/
│   ├── PhonologicalRuleOperations.py
│   └── ...domain-specific ops...
│
├── Lexicon/
│   ├── LexEntryOperations.py
│   └── ...domain-specific ops...
│
└── ... other domains ...

docs/
├── ARCHITECTURE.md               # This file - overview
├── ARCHITECTURE_WRAPPERS.md      # Wrapper classes detailed guide
├── ARCHITECTURE_COLLECTIONS.md   # Smart collections detailed guide
└── ... other documentation ...
```

---

## Getting Started

### For Users

1. **Read ARCHITECTURE_WRAPPERS.md** to understand how properties work
2. **Read ARCHITECTURE_COLLECTIONS.md** to understand filtering and display
3. **Check operation docs** for domain-specific patterns

### For Developers

1. **Read ARCHITECTURE_WRAPPERS.md** for wrapper patterns
2. **Read ARCHITECTURE_COLLECTIONS.md** for collection patterns
3. **Check CLAUDE.md** "When to Consult Claude" section for new domain implementation
4. **Review existing implementations** in Grammar, Lexicon, etc.

### For API Designers

1. **Read all three architecture documents** for full context
2. **Check CLAUDE.md** "API Design Philosophy" section
3. **Review casting and merge patterns** in lcm_casting.py
4. **Plan wrapper/collection structure** before implementation

---

## Performance Considerations

### Wrapper Overhead
- __init__: One cast_to_concrete() call (cached by pythonnet) - ~0.1ms
- Property access: Two getattr() calls - negligible
- No collection overhead for objects themselves

### Collection Overhead
- __str__() type breakdown: O(n) iteration - only when displayed
- by_type() filtering: O(n) iteration - standard collection operation
- filter() implementation: O(n) iteration - user-defined complexity

**Bottom line:** Wrappers and collections have negligible performance impact.

---

## Troubleshooting

### "AttributeError: object has no attribute X"

**Likely causes:**
- Property doesn't exist on any concrete type
- Typo in property name
- Property only available on specific concrete types

**Solution:**
- Use `get_property()` with default for optional properties
- Check wrapper documentation for available properties
- Use capability checks: `if obj.has_property_x:`

### "Unexpected type in collection"

**Likely causes:**
- Multi-type collection showing diversity (expected behavior)
- Wrong objects in collection

**Solution:**
- Print collection to see type breakdown
- Use `by_type()` to filter to specific type
- Check operation that created collection

### "Filter returns no results"

**Likely causes:**
- Filter criteria too restrictive
- Filter implementation has a bug
- No matching objects exist

**Solution:**
- Print collection before filtering to see what exists
- Simplify filter criteria one at a time
- Check collection `__str__()` output

---

## LCM Ownership Ordering

**The rule:** Factory-created LCM objects must be attached to an owning relation **before** any property setter is called on them.

**Why:** `CmObject.get_Services()` returns null until the object enters the ownership graph. Property setters route through `get_Services()` to look up writing systems, validators, and undo handlers, so a setter on an orphan object NPEs deep inside LCM with a message that does not point at the real cause.

### The four ownership relations (and the RA trap)

LCM property suffixes encode ownership:

- `...OS` (Owning Sequence) - `parent.XxxOS.Add(child)` or `parent.XxxOS.Insert(i, child)`
- `...OC` (Owning Collection) - `parent.XxxOC.Add(child)`
- `...OA` (Owning Atomic) - `parent.XxxOA = child`
- `...RA` (Reference Atomic) - **NOT owning.** Setting `obj.SomethingRA = target` records a reference *from* `obj` *to* `target`; it does not confer ownership *on* `obj`. The orphan stays an orphan.

Common pitfall: an MSA attached only via `sense.MorphoSyntaxAnalysisRA = msa` is still orphaned. Ownership of an MSA lives on the LexEntry via `entry.MorphoSyntaxAnalysesOC.Add(msa)`.

### Code shape

```python
# Right: attach first, then set properties
msa = msaFactory.Create()
entry.MorphoSyntaxAnalysesOC.Add(msa)   # must be done before setting properties
msa.PartOfSpeechRA = pos                # safe now
sense.MorphoSyntaxAnalysisRA = msa      # reference link, separate concern
```

```python
# Wrong: setter on orphan -> NPE in CmObject.get_Services()
msa = msaFactory.Create()
msa.PartOfSpeechRA = pos                # NPE: msa has no Services yet
entry.MorphoSyntaxAnalysesOC.Add(msa)
```

### Audit hint

Grep for `factory.Create()` (or `Factory.Create()`) followed by a property assignment with no intervening `OS.Add(`, `OC.Add(`, `OA =`, or `OS.Insert(` line. Carry forward the convention comment `# must be done before setting properties` on the attach line - the codebase uses it as a marker, and consistency helps future audits.

**Historical reference:** This pattern was hardened across nine outlier sites in Phase 2 of `plans/flexlibs-issues-2026-05.md`, closing MattGyverLee/flexlibs#4, #6, #7, and #8 (closed 2026-05).

---

## See Also

- **ARCHITECTURE_WRAPPERS.md** - Comprehensive wrapper classes guide
- **ARCHITECTURE_COLLECTIONS.md** - Comprehensive smart collections guide
- **CLAUDE.md** - Design philosophy, conventions, and when to consult
- **README.rst** - User-facing documentation
- **EXCEPTION_HANDLING.md** - Error handling patterns
