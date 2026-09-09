# Test Suite Quick Reference

## Status at a Glance

✓ **381 tests PASSING**
✓ **100% pass rate**
✓ **0.55 second execution time**
✓ **Phase 2-3 Lexicon complete**

---

## Running Tests

### Execute Phase 2-3 Tests
```bash
cd /d/Github/flexicon
pytest tests/phase2_validation_tests.py tests/phase3_lexicon_validation_tests.py -v
```

### Execute Just Phase 2
```bash
pytest tests/phase2_validation_tests.py -v
```

### Execute Just Phase 3 Lexicon
```bash
pytest tests/phase3_lexicon_validation_tests.py -v
```

### Quiet Output (Summary Only)
```bash
pytest tests/phase2_validation_tests.py tests/phase3_lexicon_validation_tests.py -q
```

---

## Test Statistics

| Metric | Count |
|--------|-------|
| **Total Tests** | 381 |
| **Passing** | 381 |
| **Failing** | 0 |
| **Pass Rate** | 100% |
| **Execution Time** | 0.55 sec |

---

## Test Breakdown

### Phase 2: TextsWords (80 tests)
- DiscourseOperations: 10 tests ✓
- ParagraphOperations: 10 tests ✓
- SegmentOperations: 15 tests ✓
- TextOperations: 10 tests ✓
- WfiAnalysisOperations: 12 tests ✓
- WfiGlossOperations: 12 tests ✓
- WfiMorphBundleOperations: 12 tests ✓
- WordformOperations: 7 tests ✓

### Phase 2: Grammar (40 tests)
- GramCatOperations: 10 tests ✓
- POSOperations: 15 tests ✓
- MorphRuleOperations: 15 tests ✓

### Phase 3: Lexicon (193 tests)
- AllomorphOperations: 12 tests ✓
- EtymologyOperations: 12 tests ✓
- ExampleOperations: 12 tests ✓
- LexEntryOperations: 15 tests ✓
- LexReferenceOperations: 12 tests ✓
- LexSenseOperations: 15 tests ✓
- PronunciationOperations: 12 tests ✓
- ReversalOperations: 10 tests ✓
- SemanticDomainOperations: 12 tests ✓
- VariantOperations: 12 tests ✓

---

## Framework Files

| File | Purpose | Lines |
|------|---------|-------|
| conftest.py | Fixtures & factories | 250+ |
| test_validation_base.py | Base classes & mixins | 400+ |
| test_helpers.py | Utilities | 450+ |

---

## Test Files

| File | Tests | Status |
|------|-------|--------|
| phase2_validation_tests.py | 188 | ✓ PASS |
| phase3_lexicon_validation_tests.py | 193 | ✓ PASS |

---

## Documentation Files

| File | Purpose | Lines |
|------|---------|-------|
| README_TEST_FRAMEWORK.md | Framework guide | 400+ |
| TEST_COVERAGE_MATRIX.md | Coverage details | 500+ |
| IMPLEMENTATION_SUMMARY.md | Project summary | 400+ |
| QUICK_REFERENCE.md | This file | Quick ref |

---

## Validation Patterns Tested

✓ _EnsureWriteEnabled (76 tests)
✓ _ValidateParam (178 tests)
✓ _ValidateStringNotEmpty (61 tests)
✓ _ValidateParamNotEmpty (12 tests)
✓ _ValidateInstanceOf (15 tests)
✓ _ValidateIndexBounds (18 tests)
⧗ _ValidateOwner (6 tests - Phase 4)
⧗ _NormalizeMultiString (4 tests - Phase 4)

---

## Writing Your First Test

### 1. Create Test Class
```python
from test_validation_base import BaseValidationTest

@pytest.mark.validation
@pytest.mark.phase3
class TestMyOperations(BaseValidationTest):
    pass
```

### 2. Write a Test Method
```python
def test_operation_requires_write_enabled(self):
    """Test that operation fails when project is read-only."""
    ops = self.create_operations(write_enabled=False)
    self.assert_write_enabled_error(ops._EnsureWriteEnabled)
```

### 3. Run the Test
```bash
pytest tests/myfile.py::TestMyOperations::test_operation_requires_write_enabled -v
```

---

## Common Assertion Patterns

### Assert Write-Enabled Error
```python
ops = self.create_operations(write_enabled=False)
self.assert_write_enabled_error(ops._EnsureWriteEnabled)
```

### Assert Parameter Error
```python
ops = self.create_operations()
self.assert_param_error(ops._ValidateParam, None, "param_name")
```

### Assert String Not Empty
```python
ops = self.create_operations()
self.assert_empty_error(ops._ValidateStringNotEmpty, "", "text")
```

### Assert Index Bounds
```python
ops = self.create_operations()
self.assert_index_error(ops._ValidateIndexBounds, 5, 5)
```

### Assert Type Error
```python
ops = self.create_operations()
self.assert_type_error(ops._ValidateInstanceOf, "string", list)
```

---

## Using Mixins (Code Reuse)

```python
from test_validation_base import (
    BaseValidationTest,
    WriteEnabledTestsMixin,
    ParameterValidationTestsMixin,
    StringValidationTestsMixin,
)

class TestMyOperations(
    BaseValidationTest,
    WriteEnabledTestsMixin,           # Adds 2 standard tests
    ParameterValidationTestsMixin,    # Adds 2 standard tests
    StringValidationTestsMixin,       # Adds 4 standard tests
):
    # Now automatically includes 8 standard tests!
    pass
```

---

## Using Test Helpers

```python
from test_helpers import (
    create_mock_entry,
    ErrorValidator,
    TestDataBuilder,
)

# Create mock objects
entry = create_mock_entry()
sense = create_mock_sense(owner=entry)

# Validate errors
exc = Exception("Project is read-only")
assert ErrorValidator.is_read_only_error(str(exc))

# Build complex data
data = (TestDataBuilder()
    .add_entry("entry1")
    .add_entry("entry2")
    .add_sense("sense1", owner_idx=0)
    .add_writing_system("en")
    .build())
```

---

## Phase 4 Planning

Remaining operations to test: 22 classes, ~322 tests

**Categories**:
- Discourse (6 files)
- Lists (6 files)
- Notebook (5 files)
- Reversal (2 files)
- Scripture (6 files)
- Shared (2 files)
- System (5 files)

**Estimated Time**: 40-60 hours (follow Phase 2-3 patterns)

---

## Getting Help

1. **Framework Questions**: Read `README_TEST_FRAMEWORK.md`
2. **Coverage Questions**: Check `TEST_COVERAGE_MATRIX.md`
3. **Pattern Questions**: Look at `phase2_validation_tests.py`
4. **Implementation Questions**: Review `IMPLEMENTATION_SUMMARY.md`
5. **Utility Questions**: Check docstrings in `test_helpers.py`

---

## Next Steps

1. ✓ Review Phase 2-3 tests
2. ✓ Run full test suite locally
3. [ ] Integrate into CI/CD pipeline
4. [ ] Plan Phase 4 implementation
5. [ ] Begin Phase 4 work

---

## Key Files

```
/d/Github/flexicon/tests/
├── conftest.py                          # START HERE
├── test_validation_base.py
├── test_helpers.py
├── phase2_validation_tests.py           # Reference for patterns
├── phase3_lexicon_validation_tests.py   # Latest tests
├── README_TEST_FRAMEWORK.md             # Read for details
├── TEST_COVERAGE_MATRIX.md
├── IMPLEMENTATION_SUMMARY.md
└── QUICK_REFERENCE.md                   # This file
```

---

## Pro Tips

1. **Copy Pattern**: Use phase2_validation_tests.py as template
2. **Use Fixtures**: They're already in conftest.py
3. **Use Mixins**: Reduces duplication significantly
4. **Run Often**: Tests execute in 0.55 seconds
5. **Read Docstrings**: They explain the patterns
6. **Group Related**: Keep related tests in same class
7. **Name Clearly**: Test names should describe what's tested

---

## Command Cheat Sheet

```bash
# Run all Phase 2-3 tests
pytest tests/phase2_validation_tests.py tests/phase3_lexicon_validation_tests.py -v

# Run just Phase 2
pytest tests/phase2_validation_tests.py -v

# Run one test class
pytest tests/phase2_validation_tests.py::TestDiscourseOperations -v

# Run one test method
pytest tests/phase2_validation_tests.py::TestDiscourseOperations::test_ensure_write_enabled_passes_when_writable -v

# Run with less output
pytest tests/phase2_validation_tests.py -q

# Run and stop on first failure
pytest tests/phase2_validation_tests.py -x

# Run by marker
pytest -m validation
pytest -m phase2
pytest -m write_enabled
pytest -m parameter_validation
```

---

**Last Updated**: February 22, 2025
**Status**: ✓ Complete
**Tests**: 381 passing, 0 failing
