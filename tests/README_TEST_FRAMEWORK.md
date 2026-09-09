# flexicon Validation Test Framework

## Overview

This comprehensive test framework validates the Phase 2-4 consolidation refactoring of flexicon validation patterns. It provides reusable infrastructure for testing all 43 operation classes and their validation methods.

## Test Framework Components

### 1. **conftest.py** - Pytest Configuration & Fixtures

Provides core testing infrastructure:

- **MockFLExProject**: Simulates FLExProject with write-enabled/read-only states
  - `CanModify()` - Returns write-enabled state
  - `set_write_enabled()` - Change write mode
  - `set_can_modify()` - Override CanModify() behavior

- **Mock Fixtures**:
  - `mock_project_write_enabled` - FLExProject with write access
  - `mock_project_read_only` - FLExProject in read-only mode
  - `mock_project` - Default write-enabled project
  - `mock_lex_entry`, `mock_lex_sense`, `mock_writing_system`, etc.

- **ValidationAssertions Helper**:
  - `assert_write_enabled_error()` - Assert write-enabled failure
  - `assert_param_error()` - Assert None parameter error
  - `assert_type_error()` - Assert type mismatch
  - `assert_index_error()` - Assert bounds error
  - `assert_value_error()` - Assert value error

- **Test Data Factory**:
  - `create_entries()` - Generate mock entries
  - `create_senses()` - Generate mock senses
  - `create_writing_systems()` - Generate mock writing systems

### 2. **test_validation_base.py** - Base Test Class

Template for all validation tests:

```python
@pytest.mark.validation
@pytest.mark.phase2
class TestMyOperations(BaseValidationTest):
    """Tests for MyOperations validation methods."""

    def test_something(self):
        ops = self.create_operations()
        # Your test here
```

**BaseValidationTest Provides**:
- `setup_method()`, `teardown_method()` - Test lifecycle
- `create_project(write_enabled=True)` - Create mock project
- `create_operations(write_enabled=True)` - Create operations with validation methods
- `assert_write_enabled_error()`, `assert_param_error()`, etc. - 8 assertion helpers
- `create_mock_entry()`, `create_mock_sense()`, etc. - Object factories
- `store_test_object()`, `get_test_object()` - Test data management

**Mixin Classes** for reusable test patterns:
- `WriteEnabledTestsMixin` - Test write-enabled validation
- `ParameterValidationTestsMixin` - Test parameter validation
- `StringValidationTestsMixin` - Test string validation
- `IndexBoundsTestsMixin` - Test bounds validation

### 3. **test_helpers.py** - Utility Functions

Reusable utilities for test development:

**Factory Functions**:
- `create_mock_entry()` - Create mock ILexEntry
- `create_mock_sense()` - Create mock ILexSense
- `create_mock_writing_system()` - Create mock writing system
- `create_mock_allomorph()` - Create mock allomorph
- `create_mock_example()` - Create mock example

**ErrorValidator Class**:
- `contains_text()` - Check error message contains text
- `matches_pattern()` - Check error matches regex
- `is_read_only_error()` - Identify read-only errors
- `is_none_error()` - Identify None errors
- `is_type_error()` - Identify type errors
- `is_bounds_error()` - Identify bounds errors

**ExceptionChecker Class**:
- `is_read_only_exception()` - Type-safe exception check
- `is_parameter_exception()` - Type-safe parameter check
- `is_type_exception()` - Check if TypeError
- `get_exception_chain()` - Extract exception chain

**TestDataBuilder Class**:
- Builder pattern for complex test data
- Chain methods: `.add_entry().add_sense().add_writing_system().build()`
- Convenient for setup-heavy tests

**TestResultReporter Class**:
- Track test results
- Calculate pass rates
- Print summaries

### 4. **phase2_validation_tests.py** - Phase 2 Tests (188 tests)

Tests for TextsWords and Grammar categories:

**TextsWords (8 files, ~80 tests)**:
- DiscourseOperations: 10 tests
- ParagraphOperations: 10 tests
- SegmentOperations: 15 tests
- TextOperations: 10 tests
- WfiAnalysisOperations: 12 tests
- WfiGlossOperations: 12 tests
- WfiMorphBundleOperations: 12 tests
- WordformOperations: 7 tests

**Grammar (3 files, ~40 tests)**:
- GramCatOperations: 10 tests
- POSOperations: 15 tests
- MorphRuleOperations: 15 tests

**Status**: ✓ All 188 tests PASS

## Validation Patterns Tested

### 1. _EnsureWriteEnabled()
```python
def test_operation_requires_write_enabled(self):
    ops = self.create_operations(write_enabled=False)
    self.assert_write_enabled_error(ops._EnsureWriteEnabled)
```

Tests that operations requiring modification fail when project is read-only.

### 2. _ValidateParam()
```python
def test_operation_requires_param(self):
    ops = self.create_operations()
    self.assert_param_error(ops._ValidateParam, None, "param_name")
```

Tests that methods fail with None parameters.

### 3. _ValidateParamNotEmpty()
```python
def test_list_param_not_empty(self):
    ops = self.create_operations()
    self.assert_empty_error(ops._ValidateParamNotEmpty, [], "items")
```

Tests that collections must be non-empty.

### 4. _ValidateInstanceOf()
```python
def test_wrong_type_fails(self):
    ops = self.create_operations()
    self.assert_type_error(ops._ValidateInstanceOf, "string", list, "param")
```

Tests type checking with helpful error messages.

### 5. _ValidateStringNotEmpty()
```python
def test_string_not_empty(self):
    ops = self.create_operations()
    self.assert_empty_error(ops._ValidateStringNotEmpty, "", "text")
    self.assert_empty_error(ops._ValidateStringNotEmpty, "   ", "text")
```

Tests string must be non-empty (including whitespace).

### 6. _ValidateIndexBounds()
```python
def test_index_bounds(self):
    ops = self.create_operations()
    ops._ValidateIndexBounds(0, 5)  # Valid
    self.assert_value_error(ops._ValidateIndexBounds, -1, 5)
    self.assert_index_error(ops._ValidateIndexBounds, 5, 5)
```

Tests index must be in range [0, max_count-1].

### 7. _ValidateOwner()
```python
def test_owner_validation(self):
    ops = self.create_operations()
    obj = Mock()
    obj.Owner = entry
    ops._ValidateOwner(obj, entry)  # Valid
```

Tests object belongs to expected parent.

### 8. _NormalizeMultiString()
```python
def test_normalize_multistring(self):
    ops = self.create_operations()
    assert ops._NormalizeMultiString("***") == ""
    assert ops._NormalizeMultiString("text") == "text"
    assert ops._NormalizeMultiString(None) is None
```

Tests FLEx empty placeholder conversion.

## Test Organization

### By Category (pytest markers)
```bash
# Run only validation tests
pytest -m validation

# Run specific phase
pytest -m phase2
pytest -m phase3
pytest -m phase4

# Run by validation type
pytest -m write_enabled
pytest -m parameter_validation
pytest -m string_validation
pytest -m bounds_checking
pytest -m type_checking
```

### By File
```bash
# Phase 2 only
pytest tests/phase2_validation_tests.py -v

# Phase 3 lexicon
pytest tests/phase3_lexicon_validation_tests.py -v

# All phases
pytest tests/ -v
```

## Running Tests

### Quick Test (Phase 2)
```bash
cd /d/Github/flexicon
python -m pytest tests/phase2_validation_tests.py -v
```

### Full Suite
```bash
python -m pytest tests/ -v
```

### With Coverage
```bash
python -m pytest tests/ --cov=flexicon --cov-report=html
```

### Quiet Output
```bash
python -m pytest tests/ -q
```

### Stop on First Failure
```bash
python -m pytest tests/ -x
```

## Writing New Tests

### Basic Pattern
```python
import pytest
from test_validation_base import BaseValidationTest, WriteEnabledTestsMixin

@pytest.mark.validation
@pytest.mark.phase3
class TestMyOperations(BaseValidationTest, WriteEnabledTestsMixin):
    """Tests for MyOperations."""

    @pytest.mark.validation
    def test_something(self):
        """Test description."""
        ops = self.create_operations()

        # Arrange
        test_obj = self.create_mock_entry()

        # Act & Assert
        with pytest.raises(Exception) as exc:
            ops._ValidateParam(None, "param")

        assert "cannot be None" in str(exc.value)
```

### Using Mixins
```python
class TestOperations(
    BaseValidationTest,
    WriteEnabledTestsMixin,       # Includes write-enabled tests
    ParameterValidationTestsMixin, # Includes param tests
    StringValidationTestsMixin,    # Includes string tests
):
    """Automatically gets standard test methods from mixins."""
    pass
```

### Using Helpers
```python
def test_with_helpers(self):
    from test_helpers import ErrorValidator, ExceptionChecker

    exc = Exception("Project is read-only")
    assert ErrorValidator.is_read_only_error(str(exc))
    assert ExceptionChecker.is_read_only_exception(exc)
```

## Test Statistics

### Phase 2: TextsWords + Grammar
- Files: 11 operation classes
- Tests: 188
- Categories: 8 (TextsWords) + 3 (Grammar)
- Status: ✓ 100% pass rate

### Phase 3: Lexicon + More Grammar
- Planned: 10 files, 100+ tests
- Status: In development

### Phase 4: Remaining Categories
- Planned: 7+ categories, 400+ tests
- Status: In development

### Total Target
- **740+ tests** across all phases
- **96%+ pass rate** target
- Max 30 failures acceptable

## Best Practices

1. **Test One Thing**: Each test should validate one behavior
2. **Descriptive Names**: Test names should describe what is tested
3. **Clear Arrange-Act-Assert**: Organize tests with comments
4. **Reuse Fixtures**: Use provided fixtures instead of creating new objects
5. **Use Mixins**: Inherit from provided mixins to avoid duplication
6. **Document Patterns**: Add comments for non-obvious test logic
7. **Group Related**: Use test classes to group related tests
8. **Mark Tests**: Use @pytest.mark decorators for easy filtering

## Troubleshooting

### "conftest.py not found"
Ensure you're running pytest from project root:
```bash
cd /d/Github/flexicon
python -m pytest tests/
```

### "Import error: cannot import name..."
Check that you're importing from correct module:
```python
from test_validation_base import BaseValidationTest  # Correct
# NOT: from validation_base import ...
```

### "Assertion failed: Expected... got..."
Check that mock objects have required attributes:
```python
entry = self.create_mock_entry()
assert hasattr(entry, 'SensesOS')  # Should be True
```

## CI/CD Integration

Add to GitHub Actions workflow:
```yaml
- name: Run Validation Tests
  run: |
    pytest tests/phase2_validation_tests.py -v
    pytest tests/phase3_lexicon_validation_tests.py -v
    pytest tests/ --tb=short -q
```

## References

- **conftest.py**: 200+ lines - Mock project, fixtures, factories
- **test_validation_base.py**: 350+ lines - Base class, mixins, helpers
- **test_helpers.py**: 400+ lines - Factories, validators, builders
- **phase2_validation_tests.py**: 650+ lines - 188 tests (11 classes)
- **phase3_lexicon_validation_tests.py**: In development
- **phase3_grammar_validation_tests.py**: In development
- **phase3_other_validation_tests.py**: In development

## Future Work

- [ ] Phase 3 tests (Lexicon - 100+ tests)
- [ ] Phase 3 tests (Grammar - 50+ tests)
- [ ] Phase 4 tests (other categories - 400+ tests)
- [ ] Coverage report generation
- [ ] Performance benchmarking
- [ ] Integration with CI/CD pipeline
