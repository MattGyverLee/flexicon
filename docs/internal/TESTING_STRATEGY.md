# FLExLibs Testing Strategy

Comprehensive testing approach for the flexlibs operations framework.

**Author:** Programmer Team 3 - Test Infrastructure
**Date:** 2025-12-05
**Version:** 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Testing Levels](#testing-levels)
3. [Test Organization](#test-organization)
4. [Running Tests](#running-tests)
5. [Mock Strategy](#mock-strategy)
6. [Writing New Tests](#writing-new-tests)
7. [Detecting Breaking Changes](#detecting-breaking-changes)
8. [Coverage Goals](#coverage-goals)

---

## Overview

The flexlibs testing infrastructure uses a three-tier approach:

```
┌─────────────────────────────────────────────────┐
│  Level 3: Integration Tests                    │
│  - Require real FLEx installation              │
│  - Test against actual FLEx projects           │
│  - Verify end-to-end workflows                 │
└─────────────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────────────┐
│  Level 2: Operations Tests                     │
│  - Test individual operation classes           │
│  - Use mocks for FLEx dependencies             │
│  - Verify CRUD operations                      │
└─────────────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────────────┐
│  Level 1: Baseline Tests                       │
│  - Import verification                         │
│  - Instantiation checks                        │
│  - Inheritance validation                      │
│  - Method existence tests                      │
└─────────────────────────────────────────────────┘
```

---

## Testing Levels

### Level 1: Baseline Tests

**File:** `tests/test_operations_baseline.py`

**Purpose:** Verify that all operations classes can be imported, instantiated, and have expected structure.

**What It Tests:**
- ✓ Import all 61+ operations classes
- ✓ Instantiate with mock FLExProject
- ✓ Verify inheritance from BaseOperations
- ✓ Check for reordering methods (Sort, MoveUp, MoveDown, etc.)
- ✓ Verify common CRUD methods exist (GetAll, Create, Find, Delete)
- ✓ Domain-specific validations

**When To Run:**
- Every code change
- Before commits
- CI/CD pipeline
- Quick validation (< 5 seconds)

**Example:**
```bash
# Run baseline tests only
pytest tests/test_operations_baseline.py -v

# Run with coverage
pytest tests/test_operations_baseline.py --cov=flexlibs2.code
```

**What It Catches:**
- Import errors
- Broken inheritance
- Missing required methods
- Refactoring that breaks public API
- Typos in class/method names

**Limitations:**
- Does NOT test actual functionality
- Does NOT require FLEx installation
- Does NOT verify method behavior
- Uses mocks only

---

### Level 2: Operations Tests

**Directory:** `tests/operations/`

**Purpose:** Test individual operations classes with focus on CRUD operations and business logic.

**Test Files:**
- `test_lexentry_operations.py` - Lexical entry operations
- `test_lexsense_operations.py` - Sense operations
- `test_pos_operations.py` - Part of speech operations
- `test_text_operations.py` - Text operations
- `test_wordform_operations.py` - Wordform operations
- *(Add more as needed)*

**What It Tests:**
- ✓ Method signatures and parameters
- ✓ Property getters and setters
- ✓ Error handling and validation
- ✓ Mock object interactions
- ✓ Exception raising
- ✓ Edge cases

**When To Run:**
- During development
- Before pull requests
- Feature testing
- Regression testing

**Example:**
```bash
# Run all operations tests (unit tests only)
pytest tests/operations/ -v -m "not integration"

# Run specific operations test
pytest tests/operations/test_lexentry_operations.py -v

# Run with verbose output
pytest tests/operations/ -vv --tb=short
```

**What It Catches:**
- Parameter validation bugs
- Exception handling issues
- Property access errors
- Logic errors in validation
- Regression in refactoring

**Limitations:**
- Uses mocks, not real FLEx objects
- Cannot test actual database operations
- Cannot verify FLEx LCM integration
- Cannot test cross-object relationships

---

### Level 3: Integration Tests

**Marker:** `@pytest.mark.integration`

**Purpose:** Test against real FLEx installation with actual projects.

**What It Tests:**
- ✓ Full CRUD workflows
- ✓ Real database operations
- ✓ LCM object creation
- ✓ Cross-object relationships
- ✓ Transaction handling
- ✓ Data persistence

**Requirements:**
- FLEx 9+ installed
- Test project available
- Write access to project
- Python.NET configured

**When To Run:**
- Before releases
- After major changes
- Weekly regression testing
- Manual validation

**Example:**
```bash
# Run integration tests only
pytest tests/operations/ -v -m integration

# Run all tests including integration
pytest tests/operations/ -v

# Run integration with real project
pytest tests/operations/test_lexentry_operations.py::TestLexEntryOperationsIntegration -v
```

**What It Catches:**
- Real FLEx API changes
- Database schema issues
- LCM behavior changes
- Transaction problems
- Performance issues

**Limitations:**
- Requires FLEx installation
- Slower execution
- May modify test project
- Platform-specific issues

---

## Test Organization

### Directory Structure

```
flexlibs/
├── tests/
│   ├── test_operations_baseline.py      # Level 1: Baseline
│   ├── operations/                       # Level 2: Operations
│   │   ├── __init__.py                  # Shared fixtures
│   │   ├── test_lexentry_operations.py
│   │   ├── test_lexsense_operations.py
│   │   ├── test_pos_operations.py
│   │   ├── test_text_operations.py
│   │   └── test_wordform_operations.py
│   └── test_plans/                       # Test documentation
└── flexlibs/
    ├── code/
    │   ├── BaseOperations.py
    │   ├── Lexicon/
    │   │   ├── LexEntryOperations.py
    │   │   └── LexSenseOperations.py
    │   └── Grammar/
    │       └── POSOperations.py
    └── tests/                            # Old tests
        └── test_FLExProject.py
```

### Naming Conventions

**Test Files:**
- `test_<module>_operations.py` - For operations classes
- `test_operations_baseline.py` - For baseline tests
- `test_<feature>.py` - For feature-specific tests

**Test Classes:**
- `Test<Class>Import` - Import and instantiation
- `Test<Class>Inheritance` - BaseOperations inheritance
- `Test<Class>CRUDMethods` - CRUD method existence
- `Test<Class>PropertyGetters` - Property getter methods
- `Test<Class>PropertySetters` - Property setter methods
- `Test<Class>Integration` - Integration tests (marked)

**Test Methods:**
- `test_<action>_<expected_result>` - Descriptive test names
- `test_has_<method>_method` - Method existence checks
- `test_<method>_<scenario>` - Specific scenarios

---

## Running Tests

### Quick Commands

```bash
# Run everything (fast - no integration)
pytest tests/ -v -m "not integration"

# Run baseline only (fastest)
pytest tests/test_operations_baseline.py -v

# Run operations tests only
pytest tests/operations/ -v -m "not integration"

# Run integration tests only (requires FLEx)
pytest tests/operations/ -v -m integration

# Run specific test file
pytest tests/operations/test_lexentry_operations.py -v

# Run specific test class
pytest tests/operations/test_lexentry_operations.py::TestLexEntryOperationsCRUDMethods -v

# Run specific test
pytest tests/operations/test_lexentry_operations.py::TestLexEntryOperationsCRUDMethods::test_has_create_method -v

# Run with coverage
pytest tests/ --cov=flexlibs2.code --cov-report=html

# Run with verbose output
pytest tests/ -vv --tb=long

# Run in parallel (requires pytest-xdist)
pytest tests/ -n auto -m "not integration"
```

### Test Markers

Tests use pytest markers to categorize:

```python
@pytest.mark.integration  # Requires real FLEx
@pytest.mark.slow         # Takes > 1 second
@pytest.mark.skip         # Temporarily disabled
```

**Register markers in `pytest.ini`:**
```ini
[pytest]
markers =
    integration: Tests requiring real FLEx installation
    slow: Tests that take more than 1 second
```

---

## Mock Strategy

### Philosophy

**Mock vs Real FLEx:**
- **Mock for structure testing** - Verify classes, methods, signatures
- **Real FLEx for behavior testing** - Verify actual operations work
- **Balance speed and coverage** - Most tests use mocks, critical paths use real FLEx

### Mock Objects Provided

**In `tests/operations/__init__.py`:**

```python
# Mock FLExProject
mock_flex_project()  # Full mock project

# Mock LCM objects
mock_lex_entry()     # ILexEntry
mock_lex_sense()     # ILexSense
mock_pos()           # IPartOfSpeech
mock_text()          # IText
mock_wordform()      # IWfiWordform

# Mock utilities
MockLCMObject        # Base mock with Hvo, Guid
MockMultiString      # MultiString for text fields
MockOwningSequence   # Owning sequences with reordering
```

### Using Mocks in Tests

**Example: Testing with mock project**
```python
def test_create_entry(mock_flex_project):
    """Test entry creation with mock."""
    from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

    ops = LexEntryOperations(mock_flex_project)

    # This will fail with FP_ReadOnlyError
    mock_flex_project.writeEnabled = False
    with pytest.raises(FP_ReadOnlyError):
        ops.Create("test")
```

**Example: Testing with mock objects**
```python
def test_reorder_senses(mock_flex_project, mock_lex_entry):
    """Test sense reordering."""
    from flexlibs2.code.Lexicon.LexSenseOperations import LexSenseOperations

    # Add mock senses
    senses = generate_test_senses(mock_lex_entry, count=3)

    ops = LexSenseOperations(mock_flex_project)

    # Test MoveUp
    result = ops.MoveUp(mock_lex_entry, senses[2])
    assert result == 1
    assert mock_lex_entry.SensesOS[1] == senses[2]
```

### When NOT to Use Mocks

**Don't mock when:**
- Testing actual FLEx API integration
- Verifying database persistence
- Testing cross-object relationships
- Validating LCM object creation
- Performance testing

**Use integration tests instead.**

---

## Writing New Tests

### Step-by-Step Guide

**1. Start with Baseline Test**

Add your operations class to `test_operations_baseline.py`:

```python
NEW_OPERATIONS = [
    ('MyOperations', 'flexlibs2.code.MyModule.MyOperations'),
]
```

The baseline test will automatically verify:
- Import works
- Instantiation works
- Inheritance is correct
- Reordering methods exist

**2. Create Operations Test File**

Create `tests/operations/test_mymodule_operations.py`:

```python
"""
Test Suite for MyOperations

Tests for MyModule operations.
"""

import pytest
from tests.operations import mock_flex_project

class TestMyOperationsImport:
    """Test import and instantiation."""

    def test_import(self):
        from flexlibs2.code.MyModule.MyOperations import MyOperations
        assert MyOperations is not None

class TestMyOperationsCRUDMethods:
    """Test CRUD methods exist."""

    def test_has_getall(self, mock_flex_project):
        from flexlibs2.code.MyModule.MyOperations import MyOperations
        ops = MyOperations(mock_flex_project)
        assert hasattr(ops, 'GetAll')
```

**3. Add Integration Tests**

Add integration tests for critical operations:

```python
@pytest.mark.integration
class TestMyOperationsIntegration:
    """Integration tests requiring real FLEx."""

    @pytest.fixture(scope="class")
    def flex_project(self):
        from flexlibs2 import FLExInitialize, FLExCleanup, FLExProject
        FLExInitialize()
        project = FLExProject()
        project.OpenProject("TestProject", writeEnabled=True)
        yield project
        project.CloseProject()
        FLExCleanup()

    def test_create_item(self, flex_project):
        from flexlibs2.code.MyModule.MyOperations import MyOperations
        ops = MyOperations(flex_project)
        item = ops.Create("test")
        assert item is not None
        ops.Delete(item)
```

**4. Run Tests**

```bash
# Run unit tests
pytest tests/operations/test_mymodule_operations.py -v -m "not integration"

# Run integration tests
pytest tests/operations/test_mymodule_operations.py -v -m integration
```

---

## Detecting Breaking Changes

### How Tests Detect Upstream Changes

**1. Baseline Tests Catch:**
- Removed operations classes
- Changed class names
- Broken inheritance chain
- Missing required methods
- Import errors from LCM updates

**2. Operations Tests Catch:**
- Changed method signatures
- Removed methods
- Changed exception types
- Different validation logic
- New required parameters

**3. Integration Tests Catch:**
- FLEx LCM API changes
- Database schema changes
- Changed object relationships
- New FLEx versions breaking compatibility
- Performance regressions

### Example Breaking Changes

**Breaking Change: Method Renamed**
```python
# Before
def GetHeadword(entry):
    ...

# After
def GetLexemeForm(entry):  # Renamed
    ...
```

**Detected By:**
- Baseline: `test_has_getheadword_method` fails
- Operations: `test_gethead_with_mock_entry` fails

**Breaking Change: New Required Parameter**
```python
# Before
def Create(lexeme_form):
    ...

# After
def Create(lexeme_form, morph_type):  # New required param
    ...
```

**Detected By:**
- Operations: `test_create_entry` fails with TypeError
- Integration: `test_create_and_delete_entry` fails

**Breaking Change: Exception Type Changed**
```python
# Before
raise FP_ReadOnlyError()

# After
raise PermissionError()  # Different exception
    ...
```

**Detected By:**
- Operations: `test_create_requires_write_enabled` fails (wrong exception caught)

---

## Coverage Goals

### Target Coverage Levels

**Baseline Tests:** 100%
- All operations classes imported
- All classes instantiated
- All inheritance verified

**Operations Tests:** 80%
- All public methods have existence tests
- Critical methods have behavior tests
- Error paths tested with mocks

**Integration Tests:** 20%
- Critical CRUD operations
- Common workflows
- High-risk functionality

### Coverage Commands

```bash
# Generate coverage report
pytest tests/ --cov=flexlibs2.code --cov-report=html

# View coverage in browser
open htmlcov/index.html

# Generate coverage summary
pytest tests/ --cov=flexlibs2.code --cov-report=term

# Check coverage thresholds
pytest tests/ --cov=flexlibs2.code --cov-fail-under=80
```

### Coverage Exclusions

**What NOT to test:**
- Internal/private methods (prefix with `_`)
- Auto-generated code
- Third-party code
- Deprecated methods (marked for removal)

**Add pragma to exclude:**
```python
def _internal_helper():  # pragma: no cover
    """Internal method - not tested."""
    pass
```

---

## Guidelines for Contributors

### Adding New Operations Class

1. Add class to `test_operations_baseline.py` in appropriate domain list
2. Run baseline tests to verify structure
3. Create dedicated test file if class is critical
4. Add integration tests for CRUD operations
5. Update this document if adding new patterns

### Modifying Existing Operations

1. Run baseline tests first (quick check)
2. Run operations tests for affected class
3. Run integration tests if changing critical methods
4. Update tests if API changes intentionally
5. Document breaking changes in PR

### Test Maintenance

- **Keep baseline tests comprehensive** - Add ALL new operations classes
- **Keep operations tests focused** - One class per file
- **Keep integration tests minimal** - Only critical paths
- **Update mocks when LCM changes** - Keep mocks realistic
- **Document test failures** - Help others understand why tests fail

---

## Continuous Integration

### Recommended CI Pipeline

```yaml
# Example GitHub Actions workflow
name: Tests

on: [push, pull_request]

jobs:
  baseline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run baseline tests
        run: pytest tests/test_operations_baseline.py -v

  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run operations tests
        run: pytest tests/operations/ -v -m "not integration"

  integration:
    runs-on: windows-latest  # FLEx requires Windows
    steps:
      - uses: actions/checkout@v2
      - name: Run integration tests
        run: pytest tests/operations/ -v -m integration
```

### Test Stages

1. **Pre-commit** - Run baseline tests (< 5 sec)
2. **Pre-push** - Run unit tests (< 30 sec)
3. **Pull Request** - Run all tests including integration
4. **Release** - Full test suite + coverage report

---

## Troubleshooting

### Common Issues

**Problem:** `ImportError: No module named 'flexlibs'`

**Solution:** Add project root to Python path:
```bash
export PYTHONPATH=/path/to/flexlibs:$PYTHONPATH
pytest tests/
```

**Problem:** Integration tests fail with "No FLEx projects available"

**Solution:** Create a test project or skip integration tests:
```bash
pytest tests/ -v -m "not integration"
```

**Problem:** Mock objects don't behave like real LCM objects

**Solution:** Use integration tests for that scenario, or improve mocks.

**Problem:** Tests pass locally but fail in CI

**Solution:** Check for:
- Platform differences (Windows vs Linux)
- Missing dependencies
- FLEx version differences
- Test project availability

---

## Summary

### Quick Reference

| Test Level | Speed | Coverage | Requires FLEx | When to Run |
|------------|-------|----------|---------------|-------------|
| Baseline   | Fast  | Structure | No | Every change |
| Operations | Medium | Behavior | No | Before PR |
| Integration | Slow | End-to-end | Yes | Before release |

### Best Practices

✓ **DO:**
- Run baseline tests frequently
- Use mocks for unit tests
- Add integration tests for critical paths
- Update tests when APIs change
- Document new test patterns

✗ **DON'T:**
- Skip baseline tests (they're fast!)
- Use real FLEx for unit tests
- Test internal methods
- Ignore test failures
- Commit commented-out tests

---

## Appendix

### Test Statistics

**Total Operations Classes:** 61+
- Grammar: 8 classes
- Lexicon: 10 classes
- TextsWords: 8 classes
- Wordform: 4 classes
- Discourse: 6 classes
- Scripture: 6 classes
- Notebook: 5 classes
- Reversal: 2 classes
- Lists: 6 classes
- System: 5 classes
- Shared: 2 classes

**Test Files Created:**
- Baseline: 1 file (~500 lines)
- Operations: 5 files (~150 lines each)
- Shared: 1 file (~400 lines)

**Total Test Coverage:**
- Baseline tests: ~200 test cases
- Operations tests: ~100 test cases
- Integration tests: ~20 test cases

### Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Python.NET documentation](https://pythonnet.github.io/)
- [FLEx LCM API documentation](https://github.com/sillsdev/FieldWorks)

---

**Last Updated:** 2025-12-05
**Maintained By:** Programmer Team 3 - Test Infrastructure
