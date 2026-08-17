# FlexLibs2 Claude Code Guidelines

This document outlines conventions and best practices for Claude Code when working on this project.

## Project Overview

FlexLibs2 is a Python library for accessing FieldWorks Language Explorer (FLEx) projects via the Language and Culture Model (LCM) API. It provides comprehensive CRUD operations for FLEx data types across Grammar, Lexicon, Texts & Words, Notebook, Lists, and System modules.

## Code Style & Standards

### File Headers
All Python files should include a header with:
- Module name
- Brief description
- Class/Component information
- Platform info (Python, FieldWorks version)
- Copyright notice

Example:
```python
#
#   LexEntryOperations.py
#
#   Class: LexEntryOperations
#          Lexical entry operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#
```

### Module Documentation
- Use docstrings with description, usage examples, and Args/Returns sections
- Include usage examples showing how to access classes via `FLExProject`
- Document important module-level constants

### Operations Classes
- All operations inherit from `BaseOperations`
- Follow the naming pattern: `[Domain]Operations.py` (e.g., `LexEntryOperations.py`)
- Organize by FLEx domain: Grammar, Lexicon, Texts & Words, Notebook, Lists, System
- Implement CRUD methods: Create, Read, Update, Delete patterns
- Use BaseOperations validation methods for consistency

### String Handling
- Use `normalize_text()` from `Shared.string_utils` for FLEx null marker ('***') handling
- Normalize empty multilingual string fields to empty strings
- Use `best_analysis_text()` and `best_vernacular_text()` utilities for language analysis

### Logging
- Use logging module with pattern: `logger = logging.getLogger(__name__)`
- Keep logging statements focused on debugging and issue diagnosis

## Project Structure

```
flexlibs2/
├── flexlibs2/
│   ├── code/
│   │   ├── BaseOperations.py          # Parent class for all operations
│   │   ├── FLExProject.py             # Main project interface
│   │   ├── Grammar/                   # POS, Phonemes, Rules, etc.
│   │   ├── Lexicon/                   # Entries, Senses, Examples, etc.
│   │   ├── TextsWords/                # Texts, Wordforms, Analyses, etc.
│   │   ├── Notebook/                  # Notes, People, Locations, etc.
│   │   ├── Lists/                     # Publications, Agents, etc.
│   │   ├── System/                    # Writing Systems, Custom Fields, etc.
│   │   └── Shared/                    # Utilities (string_utils, filters, etc.)
│   └── sync/                          # Sync engine and related utilities
├── tests/                             # Test suites
│   ├── operations/                    # Operation-specific tests
│   └── test_*.py                      # Integration and feature tests
└── docs/                              # API documentation and guides
```

## Testing

### Test Organization
- Use `tests/operations/` for operation-specific unit tests
- Use `tests/test_*.py` for integration tests
- Test files follow pattern: `test_[feature]_[aspect].py` or `test_[module].py`
- Tests in `flexlibs2/sync/tests/` for sync engine functionality

### Test Naming
- Test classes: `Test[FeatureName]`
- Test methods: `test_[what_is_being_tested]_[expected_result]`

### Testing Framework
- Use pytest for test execution
- Maintain `.coverage` for coverage tracking
- Check `.pytest_cache/` behavior before modifying test infrastructure

## Git Conventions

### Branches
- `main` - Production-ready code
- `master` - Current development (default branch)
- Feature branches should reference issues when applicable

### Commits
- Keep commits focused and logical
- Reference relevant changes and fixes
- Include `Co-Authored-By:` footer when appropriate

### Before Committing
- Verify code follows project style
- Check that operations use BaseOperations validation
- Ensure proper error handling with FLEx-specific exceptions

## FLEx-Specific Conventions

### Exception Handling
- Import custom exceptions from `FLExProject`:
  - `FP_ReadOnlyError` - Read-only project operations
  - `FP_NullParameterError` - Null/None parameters
  - `FP_ParameterError` - Invalid parameters

### LCM Imports
- Import FLEx types from `SIL.LCModel`
- Use factory and repository interfaces for object creation
- Handle ITsString properly for multilingual text
- **Same-name fields can have different LCM types across object types.**
  For example, `Source` is `ITsString` on `ILexSense` but `IMultiString`
  on `ILexEtymology` and `ICmBaseAnnotation`. Copying a working pattern
  from one Operations class to another without checking the field's type
  on the *target* LCM interface is the root cause of issues #36/#39/#40.
  See `docs/API_ISSUES_CATEGORIZED.md` "Category 8: Same-name fields
  with different LCM types" for the current table and the correct access
  patterns.

### Write Operations
- Only perform write operations if `project.writeEnabled` is True
  (lowercase `w` -- the attribute is `writeEnabled`, not `WriteEnabled`)
- Check write permissions before attempting Create/Update/Delete operations
- Use appropriate factories for object creation

## Live LCM Verification (REQUIRED)

**Any change written against the LCM must be verified against a live FLEx
database before it is reported as done.** A mock-only pass is not
verification and must never be presented as one. "No live LCM testing was
performed" is a FAILED verification, not a safety feature -- report it as
`FAIL: unverified`, never as a clean result.

This applies to every change that touches an Operations class, a factory
call, a property setter, `FLExProject`, or the transaction/write path. It
does not apply to pure-docs, pure-typing, or pure-test-scaffolding changes.

### The two live projects

| Project | Contents | Use for | Restore |
|---------|----------|---------|---------|
| **Target** | Mostly blank scratch | **Write-path work**: create / modify / delete against a clean slate | `python scripts/restore_target.py` |
| **Sena 3** | Fully populated example | Read-path coverage, modify-pre-existing-data | `python scripts/restore_sena3.py` |

Default to **Target** for anything that writes. Reach for Sena 3 only when
the test genuinely needs pre-existing data to read or modify.

### Fixtures

- `target_project` -- in-place, write-enabled, on the real Target.
  Capture-and-restore in a `finally:`; prefix created objects `TEST_`.
- `target_sandbox` -- write-enabled on a fresh tempdir copy of the Target
  `.fwbackup`. Nothing can leak. Use for destructive tests, or whenever
  the real Target is locked by an open FieldWorks.
- `sena3_sandbox` -- same, for Sena 3.

The canonical template is `tests/operations/test_target_live_smoke.py`.
Copy its structure.

### The required invocation

Live verification runs with the fail-loud flag set:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest <your live test file> -m requires_live_project -q
```

`FLEXLIBS_REQUIRE_LIVE=1` converts every silent degradation into a hard
failure: FLEx init falling back to mocks, a locked Target, a missing
fixture. Without it, `tests/conftest.py` prints `[WARN] MOCK MODE` and the
session still passes green -- which is exactly how unverified write-path
changes have been reported as done.

**Never run bare `pytest` or `pytest --ignore=tests/contract`.** Neither
applies an `-m` filter, so both collect and EXECUTE the ~322
`requires_live_project` tests in-place against real projects.

### Evidence is mandatory

A verification claim must cite machine-checkable evidence, not prose:

1. `tests/live_status.json` must show `"run_mode": "live"`. If it says
   `"mock"`, the run proved nothing.
2. Write `specs/<feature>/evidence/live-<task>.md` containing the exact
   command, the `run_mode` value, the pre-state and post-state values read
   back from the LCM, and the pass/fail line.

"Read back from the LCM" means re-querying the object after the write --
asserting on the value you just passed in proves nothing.

### When live verification is genuinely impossible

Say so explicitly and stop; do not substitute a mock pass. Report the
blocker (locked project, missing FieldWorks, needs a human decision) and
escalate. Per the LEX crew protocol, that is a `needs_human` handoff.

## Documentation

### API Documentation
- HTML API documentation is generated and accessible via `flexlibs2.APIHelpFile`
- Keep docstrings accurate with parameter descriptions
- Update API_ISSUES_CATEGORIZED.md when API changes are made
- Document breaking changes in migration guides

### Code Comments
- Document non-obvious FLEx behavior
- Explain workarounds for LCM quirks (e.g., null marker handling)
- Include examples showing correct usage patterns

## Windows Environment

### No Emojis in Terminal Output
- Use `[OK]`, `[DONE]`, `[PASS]` instead of ✓ or ✅
- Use `[ERROR]`, `[FAIL]` instead of ✗ or ❌
- Use `[INFO]`, `[NOTE]` instead of ℹ️
- Use `[WARN]` instead of ⚠️
- Use asterisks or dashes for bullet points, not Unicode bullets

## API Design Philosophy

### Core Principle: User-Centric Not Technology-Centric

The FlexLibs2 API should match how users naturally think about objects, hiding LCM/pythonnet complexity while maximizing functionality.

**Users think in two ways simultaneously:**
- **Abstractly:** "phonological rules", "merge entries", "filter by name"
- **Concretely:** "these rules have different properties", "some types don't have outputs"

The API must support both levels without forcing users to consciously manage the complexity.

### Key Design Rules

#### 1. Hide Interface/ClassName/Casting Complexity
- Users should NEVER see `IPhSegmentRule`, `ClassName`, or casting logic
- `cast_to_concrete()` and `validate_merge_compatibility()` are for internal use only
- Objects returned from operations should work transparently across concrete types

#### 2. Maximize Functionality in Simple Queries
```python
# Good: GetAll() returns everything with type diversity visible
rules = phonRuleOps.GetAll()
print(rules)  # Shows: PhRegularRule (7), PhMetathesisRule (3), etc.

# Avoid: Forcing users to query per type
regular = phonRuleOps.GetAll(class_type='PhRegularRule')
metathesis = phonRuleOps.GetAll(class_type='PhMetathesisRule')
```

#### 3. Unify Operations Across Types
```python
# Good: Filter works across all phonological rule types
voicing_rules = phonRuleOps.GetAll().filter(name_contains='voicing')

# Avoid: Separate filters per type
regular_voicing = [r for r in regular_rules if 'voicing' in r.name]
metathesis_voicing = [r for r in metathesis_rules if 'voicing' in r.name]
```

#### 4. Provide Smart Properties and Capability Checks
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

#### 5. Warn on Type Mismatch, Don't Block
```python
# Good: Warn user, show consequences, let them decide
result = phonRuleOps.MergeObject(rule1, rule2)
# ⚠️  WARNING: Merging different rule types
# Shows what will merge, what will be lost
# Continue? (y/n):

# Avoid: Hard error that crashes
# FP_ParameterError: Cannot merge different classes
```

### Wrapper Classes Pattern

For types with multiple concrete implementations (phonological rules, MSAs, contexts), implement wrapper classes:

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

### Smart Collections Pattern

Collections returned from GetAll() should show type diversity and support unified filtering:

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

## Casting Architecture Standards

### Casting is Implementation Detail

Users never see casting. Internal architecture uses:

- `cast_to_concrete()` - Convert base interface to concrete type (internal only)
- `validate_merge_compatibility()` - Check if objects can merge safely
- `clone_properties()` - Deep clone with automatic casting

### Cloning Always Uses clone_properties()

```python
# Standard pattern for all deep cloning operations
from ..lcm_casting import clone_properties

def Duplicate(self, item_or_hvo, deep=True):
    source = self.__ResolveObject(item_or_hvo)
    destination = factory.Create()

    if deep:
        # clone_properties handles casting internally
        clone_properties(source, destination, self.project)

    return destination
```

### Merging Always Validates Type Safety

```python
# Standard pattern for all merge operations
from ..lcm_casting import validate_merge_compatibility

def MergeObject(self, survivor, victim):
    is_compatible, error_msg = validate_merge_compatibility(survivor, victim)
    if not is_compatible:
        # Warn but allow user to proceed if they choose
        print(f"WARNING: {error_msg}")
```

## When to Consult Claude

Before implementing changes that affect:
- BaseOperations validation methods (affects all operations)
- FLExProject core functionality (central interface)
- Module structure or organization
- API surface changes
- **Wrapper classes or collection patterns** - See `docs/ARCHITECTURE_WRAPPERS.md` and `docs/ARCHITECTURE_COLLECTIONS.md` for patterns first
- **Type-safe merge/clone operations** (casting architecture)

### Creating New Wrapper Classes

When implementing a wrapper for a new domain:

1. **Review** `docs/ARCHITECTURE_WRAPPERS.md` - "Creating Domain-Specific Wrappers" section
2. **Identify** the base interface and concrete types
3. **Follow** the pattern from `flexlibs2/code/Shared/wrapper_base.py`
4. **Add** type capability checks and convenience properties
5. **Consult** if wrapper needs special handling beyond standard pattern

**Reference:** `docs/ARCHITECTURE_WRAPPERS.md`

### Creating New Collection Subclasses

When implementing a collection for filtering and display:

1. **Review** `docs/ARCHITECTURE_COLLECTIONS.md` - "Creating Domain-Specific Collections" section
2. **Inherit** from `SmartCollection` (base class)
3. **Implement** the `filter()` method with domain-specific criteria
4. **Add** convenience methods for common patterns (e.g., `by_type()` variants)
5. **Consult** if collection needs complex filtering or analysis

**Reference:** `docs/ARCHITECTURE_COLLECTIONS.md`

## Key Files to Know

### Architecture & Design
- `docs/ARCHITECTURE.md` - High-level overview of wrapper + collection pattern
- `docs/ARCHITECTURE_WRAPPERS.md` - Comprehensive wrapper classes guide
- `docs/ARCHITECTURE_COLLECTIONS.md` - Comprehensive smart collections guide
- `CLAUDE.md` (this file) - Design philosophy and conventions

### Core Infrastructure
- `flexlibs2/code/BaseOperations.py` - Parent class with shared validation
- `flexlibs2/code/FLExProject.py` - Main project interface
- `flexlibs2/code/Shared/wrapper_base.py` - LCMObjectWrapper base class
- `flexlibs2/code/Shared/smart_collection.py` - SmartCollection base class
- `flexlibs2/code/lcm_casting.py` - Casting utilities (internal use only)

### Utilities & Documentation
- `flexlibs2/code/Shared/string_utils.py` - Text normalization utilities
- `flexlibs2/code/PythonicWrapper.py` - Suffix-free property access wrapper
- `docs/API_ISSUES_CATEGORIZED.md` - Known API issues and workarounds
- `docs/EXCEPTION_HANDLING.md` - Error handling patterns
- `README.rst` - User-facing documentation

## Don'ts:
- This is a Windows system; don't use emojis in console messages.
- Call Python with `python` instead of `python3`.