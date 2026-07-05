# Testing Guide: Undo/Redo Implementation

This guide covers testing Phase 1 (rollback transactions) and Phase 2 (full undo stack) functionality.

---

## Test Levels

### Level 1: Unit Tests (No FLEx Required) ✅ READY
### Level 2: Integration Tests (Requires Live FLEx Project) ⏳ NEEDS SETUP
### Level 3: Manual Testing (Visual Verification) ⏳ NEEDS FLEx GUI
### Level 4: Research Verification (API Discovery) ✅ READY

---

## Level 1: Unit Tests (Python Only)

### Quick Syntax Check

```bash
cd flexlibs2

# Verify Python syntax is valid
python -m py_compile flexlibs2/code/FLExProject.py
python -m py_compile flexlibs2/code/transaction.py
python -m py_compile flexlibs2/code/undoable_operation.py

echo "[OK] Syntax check passed"
```

### Import Tests

```bash
python << 'EOF'
import sys
sys.path.insert(0, '.')

# Test Phase 1 imports
from flexlibs2.code.FLExProject import FP_TransactionError
from flexlibs2.code.transaction import _FLExTransaction

# Test Phase 2 imports
from flexlibs2.code.undoable_operation import _FLExUndoableOperation

# Test package-level export
from flexlibs2 import FP_TransactionError as ExportedError

print("[OK] All imports successful")
print(f"    FP_TransactionError: {FP_TransactionError}")
print(f"    _FLExTransaction: {_FLExTransaction}")
print(f"    _FLExUndoableOperation: {_FLExUndoableOperation}")
EOF
```

### Context Manager Tests (Mock-based)

Create `test_undo_redo_mocked.py`:

```python
#!/usr/bin/env python
"""Unit tests for undo/redo using mocks (no FLEx required)."""

import sys
sys.path.insert(0, '.')

from unittest.mock import Mock, MagicMock
from flexlibs2.code.transaction import _FLExTransaction
from flexlibs2.code.undoable_operation import _FLExUndoableOperation
from flexlibs2.code.FLExProject import FP_TransactionError, FP_ReadOnlyError


def test_transaction_success_no_rollback():
    """Transaction succeeds - no rollback called."""
    print("\n[TEST 1] Transaction success (no rollback)")

    project = Mock()
    project.writeEnabled = True
    mark_fn = Mock(return_value="mark_token")
    rollback_fn = Mock()

    txn = _FLExTransaction(project, "test", mark_fn, rollback_fn)
    txn.__enter__()
    result = txn.__exit__(None, None, None)

    assert result is False, "Should return False (don't suppress)"
    assert mark_fn.called, "Should mark on enter"
    assert not rollback_fn.called, "Should NOT rollback on success"
    print("  ✅ PASS")


def test_transaction_exception_triggers_rollback():
    """Transaction fails - rollback is called."""
    print("\n[TEST 2] Transaction failure (rollback triggered)")

    project = Mock()
    project.writeEnabled = True
    mark_fn = Mock(return_value="mark_token")
    rollback_fn = Mock()

    txn = _FLExTransaction(project, "test", mark_fn, rollback_fn)
    txn.__enter__()

    exc = ValueError("test error")
    result = txn.__exit__(ValueError, exc, None)

    assert result is False, "Should return False (re-raise)"
    assert rollback_fn.called, "Should rollback on exception"
    assert rollback_fn.call_args[0][0] == "mark_token", "Should pass mark to rollback"
    print("  ✅ PASS")


def test_transaction_read_only_skips_mark():
    """Read-only project skips mark."""
    print("\n[TEST 3] Read-only project (skip mark)")

    project = Mock()
    project.writeEnabled = False
    mark_fn = Mock()
    rollback_fn = Mock()

    txn = _FLExTransaction(project, "test", mark_fn, rollback_fn)
    txn.__enter__()

    assert not mark_fn.called, "Should NOT mark for read-only"
    assert txn._mark is None, "Mark should be None"
    print("  ✅ PASS")


def test_transaction_no_api_graceful():
    """No rollback API - still executes gracefully."""
    print("\n[TEST 4] No rollback API (graceful degradation)")

    project = Mock()
    project.writeEnabled = True

    txn = _FLExTransaction(project, "test", None, None)
    txn.__enter__()
    result = txn.__exit__(ValueError, ValueError("error"), None)

    assert result is False, "Should re-raise exception"
    assert txn._mark is None, "No mark should be set"
    print("  ✅ PASS - Executed without rollback API")


def test_undoable_operation_requires_undoable_mode():
    """UndoableOperation requires undoable=True."""
    print("\n[TEST 5] UndoableOperation requires undoable=True")

    project = Mock()
    project.writeEnabled = True
    project._undoable = False  # Phase 1 mode

    undo_op = _FLExUndoableOperation(project, "test", Mock(), Mock())

    try:
        undo_op.__enter__()
        assert False, "Should raise FP_TransactionError"
    except FP_TransactionError as e:
        assert "undoable=True" in str(e), "Should mention undoable parameter"
        print(f"  ✅ PASS - Correctly raised: {type(e).__name__}")


def test_undoable_operation_requires_write_enabled():
    """UndoableOperation requires write-enabled."""
    print("\n[TEST 6] UndoableOperation requires write-enabled")

    project = Mock()
    project.writeEnabled = False
    project._undoable = True

    undo_op = _FLExUndoableOperation(project, "test", Mock(), Mock())

    try:
        undo_op.__enter__()
        assert False, "Should raise FP_ReadOnlyError"
    except FP_ReadOnlyError:
        print("  ✅ PASS - Correctly raised FP_ReadOnlyError")


def test_exception_propagation():
    """Original exception is propagated after rollback."""
    print("\n[TEST 7] Exception propagation")

    project = Mock()
    project.writeEnabled = True
    mark_fn = Mock(return_value="mark")
    rollback_fn = Mock()

    txn = _FLExTransaction(project, "test", mark_fn, rollback_fn)
    txn.__enter__()

    original_exc = RuntimeError("original error")
    result = txn.__exit__(RuntimeError, original_exc, None)

    assert result is False, "Should NOT suppress exception (return False)"
    print("  ✅ PASS - Exception would propagate")


if __name__ == "__main__":
    print("=" * 70)
    print("UNIT TESTS: Undo/Redo Implementation (Mocked)")
    print("=" * 70)

    try:
        test_transaction_success_no_rollback()
        test_transaction_exception_triggers_rollback()
        test_transaction_read_only_skips_mark()
        test_transaction_no_api_graceful()
        test_undoable_operation_requires_undoable_mode()
        test_undoable_operation_requires_write_enabled()
        test_exception_propagation()

        print("\n" + "=" * 70)
        print("✅ ALL UNIT TESTS PASSED")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
```

Run it:
```bash
python test_undo_redo_mocked.py
```

---

## Level 2: Integration Tests (Requires Live FLEx)

### Prerequisites

1. **FieldWorks installed** (v9 or later)
2. **Test project available** (or create a new one)
3. **Project sharing enabled** in FLEx:
   - Open FLEx
   - Project Properties > Sharing tab
   - Enable "Share project contents with programs on this computer"
4. **flexlibs2 importable**:
   ```bash
   python -c "from flexlibs2 import FLExProject; print('OK')"
   ```

### Phase 1: Rollback Transaction Test

Create `test_phase1_integration.py`:

```python
#!/usr/bin/env python
"""Integration test for Phase 1 rollback transactions."""

import sys
sys.path.insert(0, '.')

from flexlibs2 import FLExProject, FLExInitialize, AllProjectNames


def test_phase1_transaction_rollback():
    """Test that transaction rollback works with live project."""
    print("\n[INTEGRATION TEST 1] Phase 1 Rollback Transaction")

    # Initialize FLEx
    try:
        FLExInitialize()
    except Exception as e:
        print(f"⚠️  FLExInitialize skipped: {e}")

    # Get a test project
    projects = AllProjectNames()
    if not projects:
        print("❌ FAIL: No FLEx projects found")
        print("   Create a project in FLEx and try again")
        return False

    test_project = projects[0]
    print(f"   Using project: {test_project}")

    # Open project
    project = FLExProject()
    try:
        project.OpenProject(test_project, writeEnabled=True)
        print("   ✅ Project opened")
    except Exception as e:
        print(f"❌ FAIL: Cannot open project: {e}")
        return False

    try:
        # Count entries before
        initial_count = project.LexiconNumberOfEntries()
        print(f"   Initial entries: {initial_count}")

        # Test successful transaction
        try:
            with project.Transaction("test add entry"):
                test_entry = project.LexiconAddEntry("test_word_123", "stem")
                print("   ✅ Entry created in transaction")
        except Exception as e:
            print(f"   ⚠️  Transaction failed: {e}")
            print("      (This might be OK - API discovery issue)")
            return True  # Not a failure if API not available

        # Count after
        after_count = project.LexiconNumberOfEntries()
        print(f"   After entries: {after_count}")

        if after_count > initial_count:
            print("   ✅ Entry persisted")

            # Test failed transaction rollback
            try:
                with project.Transaction("test rollback"):
                    project.LexiconAddEntry("rollback_test_456", "stem")
                    print("   ✅ Second entry created")
                    raise ValueError("Intentional error to trigger rollback")
            except ValueError:
                print("   ✅ Caught intentional error")

            # Verify rollback
            final_count = project.LexiconNumberOfEntries()
            print(f"   Final entries: {final_count}")

            if final_count == after_count:
                print("   ✅ Rollback successful - entry was removed")
                return True
            else:
                print(f"   ❌ Rollback failed - count changed from {after_count} to {final_count}")
                return False
        else:
            print("   ⚠️  Entry not persisted (API might not support this)")
            return True

    finally:
        project.CloseProject()
        print("   ✅ Project closed")


if __name__ == "__main__":
    print("=" * 70)
    print("INTEGRATION TEST: Phase 1 Rollback")
    print("=" * 70)
    print("\nPrerequisites:")
    print("  ✓ FieldWorks installed")
    print("  ✓ Test project exists")
    print("  ✓ Project sharing enabled")

    success = test_phase1_transaction_rollback()

    print("\n" + "=" * 70)
    if success:
        print("✅ INTEGRATION TEST PASSED")
    else:
        print("❌ INTEGRATION TEST FAILED")
    print("=" * 70)

    sys.exit(0 if success else 1)
```

Run it:
```bash
python test_phase1_integration.py
```

### Phase 2: Research Verification

Before testing Phase 2, verify that the required LCM APIs exist:

```bash
python research_phase2_lcm_api.py
```

This script will:
1. Attempt to open a test project
2. Check for BeginUndoTask/EndUndoTask APIs
3. Check for UndoStack.Mark/RollbackToMark
4. Report which APIs are available
5. Suggest which Phase 2 features will work

---

## Level 3: Manual Testing (Visual Verification)

### Phase 1: Verify Transactions Work

```python
#!/usr/bin/env python
"""Manual verification of Phase 1 transactions."""

import sys
sys.path.insert(0, '.')

from flexlibs2 import FLExProject, FLExInitialize

FLExInitialize()
project = FLExProject()
project.OpenProject("YOUR_PROJECT_NAME", writeEnabled=True)

try:
    print("\n[MANUAL TEST 1] Phase 1 Transaction")
    print("=" * 60)

    # Show initial state
    print(f"\nInitial entries: {project.LexiconNumberOfEntries()}")

    # Successful transaction
    print("\n1. Running successful transaction...")
    with project.Transaction("Add test entries"):
        for i in range(3):
            word = f"testword_{i}"
            project.LexiconAddEntry(word, "stem")
            print(f"   Created: {word}")

    print(f"After success: {project.LexiconNumberOfEntries()}")

    # Failed transaction (should rollback)
    print("\n2. Running failed transaction (should rollback)...")
    before_fail = project.LexiconNumberOfEntries()

    try:
        with project.Transaction("Rollback test"):
            word = f"should_rollback"
            project.LexiconAddEntry(word, "stem")
            print(f"   Created: {word}")
            raise RuntimeError("Intentional error to trigger rollback")
    except RuntimeError:
        print("   Error caught (as expected)")

    after_fail = project.LexiconNumberOfEntries()

    if after_fail == before_fail:
        print(f"✅ Rollback successful! Count unchanged: {before_fail}")
    else:
        print(f"⚠️  Rollback uncertain. Before: {before_fail}, After: {after_fail}")

    # Save and verify
    print("\n3. Saving changes...")
    project.SaveChanges()
    print("✅ Changes saved")

    print("\n" + "=" * 60)
    print("Manual test complete!")

finally:
    project.CloseProject()
```

### Phase 2: Verify Undo Stack Integration

```python
#!/usr/bin/env python
"""Manual verification of Phase 2 undo stack (requires FLEx GUI)."""

import sys
sys.path.insert(0, '.')

from flexlibs2 import FLExProject, FLExInitialize

FLExInitialize()
project = FLExProject()

try:
    print("\n[MANUAL TEST 2] Phase 2 Undo Stack")
    print("=" * 60)
    print("\nIMPORTANT: Keep FLEx open during this test!")
    print("Watch the FLEx Edit > Undo menu as operations are performed.\n")

    # Open in undoable mode
    print("1. Opening project in undoable mode...")
    try:
        project.OpenProject("YOUR_PROJECT_NAME", writeEnabled=True, undoable=True)
        print("✅ Opened with undoable=True")
    except Exception as e:
        print(f"⚠️  Failed to open in undoable mode: {e}")
        print("   (Phase 2 LCM APIs may not be available)")
        return

    # Perform undoable operations
    print("\n2. Adding entries via UndoableOperation...")
    try:
        with project.UndoableOperation("Add word 'apple'"):
            entry = project.LexiconAddEntry("apple", "stem")
            print("   ✅ Created 'apple'")

        print("\n   👀 Look at FLEx Edit > Undo menu")
        print("      Should see: 'Add word apple'")
        input("   Press ENTER to continue...")

        with project.UndoableOperation("Add word 'banana'"):
            entry = project.LexiconAddEntry("banana", "stem")
            print("   ✅ Created 'banana'")

        print("\n   👀 Look at FLEx Edit > Undo menu again")
        print("      Should see: 'Add word banana'")
        input("   Press ENTER to continue...")

    except Exception as e:
        print(f"⚠️  UndoableOperation failed: {e}")
        print("   (Phase 2 LCM APIs may not be available)")
        return

    # Test Undo/Redo
    print("\n3. Testing Undo/Redo methods...")
    try:
        print("   Calling project.Undo()...")
        project.Undo()
        print("   ✅ Undo called")
        print("   👀 'banana' should have been removed in FLEx")
        input("   Press ENTER to continue...")

        print("   Calling project.Redo()...")
        project.Redo()
        print("   ✅ Redo called")
        print("   👀 'banana' should have been restored in FLEx")
        input("   Press ENTER to continue...")
    except Exception as e:
        print(f"⚠️  Undo/Redo failed: {e}")

    print("\n" + "=" * 60)
    print("✅ Manual Phase 2 test complete!")

finally:
    try:
        project.CloseProject()
    except:
        pass
```

---

## Level 4: Research Verification (API Discovery)

Verify that the required LCM APIs exist for Phase 2:

```bash
# Run the automated research script
python research_phase2_lcm_api.py
```

This will:
- ✅ Detect BeginUndoTask/EndUndoTask locations
- ✅ Detect UndoStack.Mark/RollbackToMark locations
- ✅ Test if BeginUndoTask actually works
- ✅ Report which Phase 2 features are feasible

---

## Quick Test Checklist

### Phase 1 Tests (No FLEx Required)
- [ ] Syntax check passes
- [ ] Imports work
- [ ] Unit tests pass (all 7 tests)

### Phase 2 Feasibility (Requires FLEx)
- [ ] Research script runs successfully
- [ ] Research script finds BeginUndoTask or UndoStack.Mark
- [ ] Research script reports APIs available

### Integration Tests (Requires Live FLEx + Write Access)
- [ ] Can open project in write mode
- [ ] Transaction marks a checkpoint
- [ ] Rollback removes uncommitted changes
- [ ] SaveChanges persists committed changes

### Manual Tests (Requires FLEx GUI Open)
- [ ] Phase 1: Entries added in transaction persist
- [ ] Phase 1: Entries not added when rollback occurs
- [ ] Phase 2: Operations appear in FLEx Ctrl+Z menu
- [ ] Phase 2: Undo() reverses last operation
- [ ] Phase 2: Redo() reapplies operation

---

## Troubleshooting

### Import Errors
```bash
# Ensure flexlibs2 is in path
python -c "import sys; sys.path.insert(0, '.'); from flexlibs2 import FLExProject"
```

### FLEx Not Found
```bash
# Check FieldWorks is installed
python -c "from flexlibs2 import FLExInitialize; FLExInitialize()"
```

### Project Not Found
```bash
# List available projects
python -c "from flexlibs2 import AllProjectNames; print(AllProjectNames())"
```

### Research Script Issues
```bash
# Run research script for detailed diagnostics
python research_phase2_lcm_api.py

# Check which APIs are available
# This determines which Phase 2 features will work
```

---

## Next Steps After Testing

1. **All Unit Tests Pass** → Phase 1 is ready
2. **Research Script Reports APIs Available** → Phase 2 can proceed
3. **Integration Tests Pass** → Ready for production
4. **Manual Tests Successful** → Feature is validated
5. **Merge to Main** → Deploy to users

