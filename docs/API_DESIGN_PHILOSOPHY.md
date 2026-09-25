# Flexicon API Design Philosophy

Full rationale and worked examples for the design rules summarised in
`CLAUDE.md`. `CLAUDE.md` is the binding checklist; this file is the
reference that explains and illustrates each rule.

## Core Principle: User-Centric Not Technology-Centric

The Flexicon API should match how users naturally think about objects,
hiding LCM/pythonnet complexity while maximizing functionality.

**Users think in two ways simultaneously:**

- **Abstractly:** "phonological rules", "merge entries", "filter by name"
- **Concretely:** "these rules have different properties", "some types
  don't have outputs"

The API must support both levels without forcing users to consciously
manage the complexity.

## Rule 1 -- Hide Interface/ClassName/Casting Complexity

Users should NEVER *have to* see `IPhSegmentRule`, `ClassName`, or casting
logic in the normal course of using an Operations class. The Operations
classes cast internally (in `__ResolveObject` and in collection getters)
so that objects returned from operations work transparently across
concrete types.

`validate_merge_compatibility()` is for internal use only.

`cast_to_concrete()` is **public** (`from flexicon import cast_to_concrete`,
issue #271). It is the documented *escape hatch*, not the primary remedy:
reach for it when a caller has left the wrapper API and holds raw LCM
objects, or for collections that stay legitimately polymorphic (e.g.
`ComponentLexemesRS` / `TargetsRS`, which legally mix `ILexEntry` and
`ILexSense`). Being total -- an unrecognised `ClassName` returns the object
unchanged -- it is strictly safer than the `ILexEntry(x)` workaround users
otherwise land on, which throws on a legitimately-`ILexSense` element.

The round-trip contract (every item a `GetAll()`-family method hands back
must work when passed straight into another method on that same Operations
class) is part of this rule: it is what "cast internally" means from the
caller's side. See `docs/ARCHITECTURE_WRAPPERS.md`, "The round-trip
contract", for the mechanism (`BaseOperations._UnwrapLcm`) and issue #449
for the defect it fixed.

## Rule 2 -- Maximize Functionality in Simple Queries

```python
# Good: GetAll() returns everything with type diversity visible
rules = phonRuleOps.GetAll()
print(rules)  # Shows: PhRegularRule (7), PhMetathesisRule (3), etc.

# Avoid: Forcing users to query per type
regular = phonRuleOps.GetAll(class_type='PhRegularRule')
metathesis = phonRuleOps.GetAll(class_type='PhMetathesisRule')
```

## Rule 3 -- Unify Operations Across Types

```python
# Good: Filter works across all phonological rule types
voicing_rules = phonRuleOps.GetAll().filter(name_contains='voicing')

# Avoid: Separate filters per type
regular_voicing = [r for r in regular_rules if 'voicing' in r.name]
metathesis_voicing = [r for r in metathesis_rules if 'voicing' in r.name]
```

## Rule 4 -- Provide Smart Properties and Capability Checks

```python
# Good: Works for any rule type
for rule in all_rules:
    if rule.has_output_specs:
        print(rule.output_segments)
    if rule.has_metathesis_parts:
        print("This is a metathesis rule")

# Avoid: Checking ClassName or manual casting
if rule.ClassName == 'PhRegularRule':
    concrete = IPhRegularRule(rule)
    print(concrete.RightHandSidesOS)
```

## Rule 5 -- Don't Add a Flag for Behaviour That Should Be Unconditional

**The caller-managed-flag anti-pattern:** do not add a keyword argument
that makes the caller opt in to *correct* behaviour, when the rest of the
library already provides that behaviour for free.

```python
# Avoid: correctness becomes the caller's problem, and the sites that
# needed fixing get to stay wrong by default.
def SetText(self, para, content, preserve_whitespace=False): ...

# Good: fix the behaviour unconditionally.
def SetText(self, para, content): ...   # always preserves the payload
```

The test is whether a house convention already exists. If most of the
library already does the right thing and a handful of sites do not, those
sites are **outliers to be conformed**, and a flag merely licenses them to
stay outliers. `specs/242-paragraph-whitespace/spec.md` C8 rejected a
`preserve_whitespace=` kwarg on exactly this ground: 82 sibling writer
sites already persisted the caller's value unmodified while only 12 did
not.

This does **not** forbid every behavioural keyword. A flag is legitimate
when correct behaviour is genuinely call-site-dependent -- for example
`normalize_match_key(text, casefold=...)`
(`flexicon/code/Shared/string_utils.py:50`), where case sensitivity really
does differ per lookup and both branches are exercised in earnest. The
anti-pattern is specifically a flag whose `False` default preserves a bug.

## Rule 6 -- Warn on Type Mismatch, Don't Block

```python
# Good: Warn user, show consequences, let them decide
result = phonRuleOps.MergeObject(rule1, rule2)
# [WARN] Merging different rule types
# Shows what will merge, what will be lost
# Continue? (y/n):

# Avoid: Hard error that crashes
# FP_ParameterError: Cannot merge different classes
```

## Wrapper Classes Pattern

For types with multiple concrete implementations (phonological rules,
MSAs, contexts), implement wrapper classes. The canonical base is
`flexicon/code/Shared/wrapper_base.py`; the comprehensive guide, including
"Creating Domain-Specific Wrappers", is `docs/ARCHITECTURE_WRAPPERS.md`.

```python
class PhonologicalRule:
    """
    Wrapper around IPhSegmentRule that provides unified interface.

    Handles casting transparently so users don't see interface complexity.
    """
    def __init__(self, lcm_obj):
        self._obj = lcm_obj
        self._concrete = cast_to_concrete(lcm_obj)

    def __getattr__(self, name):
        # Try concrete type first (more specific)
        try:
            return getattr(self._concrete, name)
        except AttributeError:
            # Fall back to base interface
            return getattr(self._obj, name)

    # Convenience properties that work across all types
    @property
    def input_contexts(self):
        return list(self._concrete.StrucDescOS)

    # Smart properties that return what exists
    @property
    def output_segments(self):
        if hasattr(self._concrete, 'RightHandSidesOS'):
            return list(self._concrete.RightHandSidesOS)
        return []

    # Capability checks instead of type checking
    @property
    def has_output_specs(self):
        return hasattr(self._concrete, 'RightHandSidesOS')
```

### Creating a new wrapper

1. **Review** `docs/ARCHITECTURE_WRAPPERS.md` -- "Creating Domain-Specific
   Wrappers" section
2. **Identify** the base interface and concrete types
3. **Follow** the pattern from `flexicon/code/Shared/wrapper_base.py`
4. **Add** type capability checks and convenience properties
5. **Route every resolver through `BaseOperations._UnwrapLcm`** before it
   performs a pythonnet interface cast, an equality/`IndexOf`/`Remove`
   check, or any other raw-LCM-sequence operation -- if the new wrapper's
   `GetAll()` (or any other collection-returning method) can hand back
   wrapped items, every method that accepts one of those items back must
   unwrap it first. See `docs/ARCHITECTURE_WRAPPERS.md`, "The round-trip
   contract" (issue #449).
6. **Consult** if the wrapper needs special handling beyond the standard
   pattern

## Smart Collections Pattern

Collections returned from `GetAll()` should show type diversity and
support unified filtering. The base class is
`flexicon/code/Shared/smart_collection.py`; the comprehensive guide is
`docs/ARCHITECTURE_COLLECTIONS.md`.

```python
class RuleCollection:
    """
    Smart collection that manages type diversity transparently.
    """
    def __str__(self):
        # Show type summary on display
        return "Phonological Rules Summary (12 rules)\n" + \
               "  PhRegularRule: 7 (58%)\n" + \
               "  PhMetathesisRule: 3 (25%)\n" + \
               "  PhReduplicationRule: 2 (17%)"

    def filter(self, **criteria):
        # Filter works across all types
        return RuleCollection(
            [r for r in self.rules if self._matches(r, criteria)]
        )

    def by_type(self, class_type):
        # Optional type filtering if user wants it
        return RuleCollection([r for r in self.rules if r.ClassName == class_type])
```

### Creating a new collection subclass

1. **Review** `docs/ARCHITECTURE_COLLECTIONS.md` -- "Creating
   Domain-Specific Collections" section
2. **Inherit** from `SmartCollection` (base class)
3. **Implement** the `filter()` method with domain-specific criteria
4. **Add** convenience methods for common patterns (e.g. `by_type()`
   variants)
5. **Consult** if the collection needs complex filtering or analysis

## Casting Architecture Standards

### Casting is mostly an implementation detail

Users should not need to cast when going through an Operations class. The
casting utilities in `flexicon/code/lcm_casting.py` are:

- `cast_to_concrete()` -- Convert base interface to concrete type.
  **Public** (`from flexicon import cast_to_concrete`, issue #271); used
  internally throughout, and exported as the documented escape hatch for
  direct-LCM work and legitimately-polymorphic collections. Total: an
  unrecognised `ClassName`, a missing `ClassName`, or a failed CLR cast all
  return the object unchanged, so guard derived-member access with
  `hasattr`.
- `validate_merge_compatibility()` -- Check if objects can merge safely
  (internal only)
- `clone_properties()` -- Deep clone with automatic casting (internal only)

### Cloning always uses clone_properties()

```python
from ..lcm_casting import clone_properties

def Duplicate(self, item_or_hvo, deep=True):
    source = self.__ResolveObject(item_or_hvo)
    destination = factory.Create()

    if deep:
        # clone_properties handles casting internally
        clone_properties(source, destination, self.project)

    return destination
```

### Merging always validates type safety

```python
from ..lcm_casting import validate_merge_compatibility

def MergeObject(self, survivor, victim):
    is_compatible, error_msg = validate_merge_compatibility(survivor, victim)
    if not is_compatible:
        # Warn but allow user to proceed if they choose
        print(f"WARNING: {error_msg}")
```

## When to Consult Before Implementing

Changes that affect:

- `BaseOperations` validation methods (affects all operations)
- `FLExProject` core functionality (central interface)
- Module structure or organization
- API surface changes
- Wrapper classes or collection patterns -- read
  `docs/ARCHITECTURE_WRAPPERS.md` and `docs/ARCHITECTURE_COLLECTIONS.md`
  first
- Type-safe merge/clone operations (casting architecture)
