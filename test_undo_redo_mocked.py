#!/usr/bin/env python
"""Unit tests for undo/redo using mocks (no FLEx required)."""

import sys

sys.path.insert(0, ".")

from unittest.mock import Mock
from flexlibs2.code.transaction import _FLExTransaction
from flexlibs2.code.undoable_operation import _FLExUndoableOperation
from flexlibs2.code.FLExProject import FP_TransactionError, FP_ReadOnlyError


def test_transaction_success_no_rollback():
    """Transaction succeeds - no rollback called."""
    print("\n[TEST 1] Transaction success (no rollback)...", end=" ")

    project = Mock()
    project.writeEnabled = True
    mark_fn = Mock(return_value="mark_token")
    rollback_fn = Mock()

    txn = _FLExTransaction(project, "test", mark_fn, rollback_fn)
    txn.__enter__()
    result = txn.__exit__(None, None, None)

    assert result is False
    assert mark_fn.called
    assert not rollback_fn.called
    print("[PASS]")


def test_transaction_exception_triggers_rollback():
    """Transaction fails - rollback is called."""
    print("[TEST 2] Transaction failure (rollback triggered)...", end=" ")

    project = Mock()
    project.writeEnabled = True
    mark_fn = Mock(return_value="mark_token")
    rollback_fn = Mock()

    txn = _FLExTransaction(project, "test", mark_fn, rollback_fn)
    txn.__enter__()

    exc = ValueError("test error")
    result = txn.__exit__(ValueError, exc, None)

    assert result is False
    assert rollback_fn.called
    print("[PASS]")


def test_transaction_read_only_skips_mark():
    """Read-only project skips mark."""
    print("[TEST 3] Read-only project (skip mark)...", end=" ")

    project = Mock()
    project.writeEnabled = False
    mark_fn = Mock()
    rollback_fn = Mock()

    txn = _FLExTransaction(project, "test", mark_fn, rollback_fn)
    txn.__enter__()

    assert not mark_fn.called
    assert txn._mark is None
    print("[PASS]")


def test_transaction_no_api_graceful():
    """No rollback API - still executes gracefully."""
    print("[TEST 4] No rollback API (graceful degradation)...", end=" ")

    project = Mock()
    project.writeEnabled = True

    txn = _FLExTransaction(project, "test", None, None)
    txn.__enter__()
    result = txn.__exit__(ValueError, ValueError("error"), None)

    assert result is False
    assert txn._mark is None
    print("[PASS]")


def test_undoable_operation_requires_undoable_mode():
    """UndoableOperation requires undoable=True."""
    print("[TEST 5] UndoableOperation requires undoable=True...", end=" ")

    project = Mock()
    project.writeEnabled = True
    project._undoable = False

    undo_op = _FLExUndoableOperation(project, "test")

    try:
        undo_op.__enter__()
        assert False
    except FP_TransactionError:
        print("[PASS]")


def test_undoable_operation_requires_write_enabled():
    """UndoableOperation requires write-enabled."""
    print("[TEST 6] UndoableOperation requires write-enabled...", end=" ")

    project = Mock()
    project.writeEnabled = False
    project._undoable = True

    undo_op = _FLExUndoableOperation(project, "test")

    try:
        undo_op.__enter__()
        assert False
    except FP_ReadOnlyError:
        print("[PASS]")


def test_exception_propagation():
    """Original exception is propagated after rollback."""
    print("[TEST 7] Exception propagation...", end=" ")

    project = Mock()
    project.writeEnabled = True
    mark_fn = Mock(return_value="mark")
    rollback_fn = Mock()

    txn = _FLExTransaction(project, "test", mark_fn, rollback_fn)
    txn.__enter__()

    original_exc = RuntimeError("original error")
    result = txn.__exit__(RuntimeError, original_exc, None)

    assert result is False
    print("[PASS]")


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
        print("[OK] ALL 7 UNIT TESTS PASSED")
        print("=" * 70)
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
