#
#   test_transaction_rollback.py
#
#   Class: TestTransactionRollback
#          Mock-based unit tests for _FLExTransaction and
#          _NestingAwareTransaction failure/rollback paths.
#          No live FLEx project or pythonnet required.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import contextlib
import pytest
from unittest.mock import MagicMock, Mock, call


# ---------------------------------------------------------------------------
# Helpers: build minimal mock projects
# ---------------------------------------------------------------------------

def _make_phase1_project(mark_return="mark-token-1"):
    """
    Phase 1 project (_undoable=False) with a real Mark API double.

    Returns (project, mark_mock, rollback_mock) so callers can assert
    invocation counts.
    """
    mark_mock = Mock(return_value=mark_return)
    rollback_mock = Mock()

    # _FLExTransaction uses project.writeEnabled to decide whether to mark.
    project = Mock()
    project.writeEnabled = True
    project._undoable = False
    project._transaction_depth = 0

    # project.Transaction(label) is called by _NestingAwareTransaction.
    # We return a real _FLExTransaction wired to our mark/rollback doubles.
    def _make_flex_transaction(label="transaction"):
        from flexlibs2.code.transaction import _FLExTransaction
        return _FLExTransaction(project, label, mark_mock, rollback_mock)

    project.Transaction = Mock(side_effect=_make_flex_transaction)
    project.UndoableOperation = Mock(
        side_effect=lambda label: contextlib.nullcontext()
    )
    return project, mark_mock, rollback_mock


def _make_phase1_project_no_mark():
    """
    Phase 1 project where _GetTransactionAPI returned (None, None) --
    simulates no LCM rollback API found.
    """
    project, _, _ = _make_phase1_project()

    def _make_flex_transaction_no_mark(label="transaction"):
        from flexlibs2.code.transaction import _FLExTransaction
        return _FLExTransaction(project, label, None, None)

    project.Transaction = Mock(side_effect=_make_flex_transaction_no_mark)
    return project


def _make_phase2_project():
    """
    Phase 2 project (_undoable=True, depth=0).
    UndoableOperation returns a real nullcontext so __enter__/__exit__ work.
    """
    project = Mock()
    project.writeEnabled = True
    project._undoable = True
    project._transaction_depth = 0
    project.UndoableOperation = Mock(
        side_effect=lambda label: contextlib.nullcontext()
    )
    project.Transaction = Mock(
        side_effect=lambda label="transaction": contextlib.nullcontext()
    )
    return project


# ---------------------------------------------------------------------------
# Phase 1: rollback-on-exception
# ---------------------------------------------------------------------------

class TestPhase1Rollback:
    """PHASE 1: _FLExTransaction calls RollbackToMark on exception."""

    def test_rollback_called_on_exception(self):
        """
        Entering _TransactionCM (Phase 1) and raising inside the body
        must invoke RollbackToMark with the mark token returned by Mark().
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project, mark_mock, rollback_mock = _make_phase1_project(
            mark_return="sentinel-mark"
        )

        with pytest.raises(RuntimeError, match="intentional"):
            with _NestingAwareTransaction(project, "test-rollback"):
                raise RuntimeError("intentional")

        rollback_mock.assert_called_once_with("sentinel-mark")

    def test_no_rollback_on_clean_exit(self):
        """
        When no exception is raised, RollbackToMark must NOT be called.
        This is the normal commit path.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project, mark_mock, rollback_mock = _make_phase1_project()

        with _NestingAwareTransaction(project, "test-commit"):
            pass  # no exception

        rollback_mock.assert_not_called()

    def test_mark_called_on_enter(self):
        """
        __enter__ must call Mark() so a rollback point exists before
        any mutations run.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project, mark_mock, rollback_mock = _make_phase1_project()

        with _NestingAwareTransaction(project, "test-mark"):
            pass

        mark_mock.assert_called_once()

    def test_original_exception_reraised_after_rollback(self):
        """
        _FLExTransaction must not suppress the original exception even
        after a successful rollback.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project, _, _ = _make_phase1_project()

        class _Sentinel(Exception):
            pass

        with pytest.raises(_Sentinel):
            with _NestingAwareTransaction(project, "test-reraise"):
                raise _Sentinel("must propagate")


# ---------------------------------------------------------------------------
# Phase 1: (None, None) mark API -- no rollback available
# ---------------------------------------------------------------------------

class TestPhase1NoMarkAPI:
    """
    PHASE 1 with no rollback API available (Domain Concern 2).

    The Phase-1 Mark/RollbackToMark API is not yet discoverable in the shipped
    LCM build (docs/internal/RESEARCH_NEEDED.md). When it resolves to (None, None) on a
    write-enabled project, _FLExTransaction degrades gracefully: it logs a
    warning and proceeds WITHOUT rollback, because raising would make every
    write impossible. The body still runs and any body exception still
    propagates (no silent swallow). A strict opt-in mode that would fail fast
    is tracked separately and is NOT the current default.
    """

    def test_none_mark_api_enters_without_raising(self):
        """
        With (None, None) mark API on a write-enabled project, entering the
        transaction must NOT raise; it degrades to no-rollback and runs the body.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase1_project_no_mark()
        body_ran = []

        with _NestingAwareTransaction(project, "test-no-mark"):
            body_ran.append(True)

        assert body_ran == [True], "body must run even when rollback API is unavailable"

    def test_none_mark_api_still_reraises_body_exception(self):
        """
        Even without a mark, a body exception must propagate (no silent
        swallow). This exercises the no-mark branch of __exit__.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase1_project_no_mark()

        with pytest.raises(ValueError, match="body error"):
            with _NestingAwareTransaction(project, "test-no-mark-reraise"):
                raise ValueError("body error")


# ---------------------------------------------------------------------------
# Phase 2: nesting depth regression-lock
# ---------------------------------------------------------------------------

class TestPhase2Nesting:
    """
    PHASE 2: regression lock for the cycle-1 nesting fix.

    Verifies:
    - depth 0  -> UndoableOperation used (outermost)
    - depth > 0 -> no-op (no undo API touched)
    - depth balanced to 0 on clean exit
    - depth balanced to 0 even when body raises
    """

    def test_outermost_uses_undoable_operation(self):
        """
        At depth 0 with _undoable=True, _NestingAwareTransaction must
        call project.UndoableOperation(), not project.Transaction().
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project()
        assert project._transaction_depth == 0

        with _NestingAwareTransaction(project, "outer"):
            pass

        project.UndoableOperation.assert_called_once_with("outer")
        project.Transaction.assert_not_called()

    def test_nested_phase2_is_noop(self):
        """
        A second _NestingAwareTransaction entered while one is already
        active (depth > 0) must NOT call UndoableOperation or Transaction.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project()

        with _NestingAwareTransaction(project, "outer"):
            # depth is now 1; inner must be a no-op
            inner = _NestingAwareTransaction(project, "inner")
            with inner:
                pass  # inner body runs without error

        # UndoableOperation called exactly once (for the outer block only).
        assert project.UndoableOperation.call_count == 1

    def test_depth_restored_on_clean_exit(self):
        """
        _transaction_depth must return to 0 after a clean exit.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project()

        with _NestingAwareTransaction(project, "outer"):
            assert project._transaction_depth == 1

        assert project._transaction_depth == 0

    def test_depth_restored_on_exception(self):
        """
        _transaction_depth must return to 0 even when the body raises.
        The depth counter must not leak across calls.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project()

        with pytest.raises(RuntimeError):
            with _NestingAwareTransaction(project, "outer-raises"):
                raise RuntimeError("boom")

        assert project._transaction_depth == 0

    def test_nested_depth_restored_on_inner_exception(self):
        """
        When the inner (no-op) block raises, both outer and inner depth
        decrements must still fire, leaving depth at 0.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project()

        with pytest.raises(RuntimeError):
            with _NestingAwareTransaction(project, "outer"):
                with _NestingAwareTransaction(project, "inner"):
                    raise RuntimeError("inner boom")

        assert project._transaction_depth == 0


# ---------------------------------------------------------------------------
# Phase 1 nesting: independent rollback points
# ---------------------------------------------------------------------------

class TestPhase1Nesting:
    """
    Phase 1 nesting is allowed and each block gets its own mark.
    Regression: depth still balances to 0 after nested Phase 1 blocks.
    """

    def test_phase1_nested_depth_balances(self):
        """
        Entering two nested _NestingAwareTransaction blocks (Phase 1)
        increments depth to 2 then restores it to 0 on exit.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project, mark_mock, rollback_mock = _make_phase1_project()

        with _NestingAwareTransaction(project, "outer"):
            assert project._transaction_depth == 1
            with _NestingAwareTransaction(project, "inner"):
                assert project._transaction_depth == 2
            assert project._transaction_depth == 1

        assert project._transaction_depth == 0

    def test_phase1_nested_mark_called_twice(self):
        """
        Two nested Phase 1 blocks each open their own _FLExTransaction,
        so Mark() is called twice (once per block).
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project, mark_mock, rollback_mock = _make_phase1_project()

        with _NestingAwareTransaction(project, "outer"):
            with _NestingAwareTransaction(project, "inner"):
                pass

        assert mark_mock.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
