#
#   test_transaction_rollback.py
#
#   Class: TestTransactionRollback
#          Mock-based unit tests for _FLExTransaction, _NestingAwareTransaction,
#          and _FLExUndoableOperation failure/rollback paths.
#          No live FLEx project or pythonnet write required -- Phase 2 tests
#          patch the UndoableUnitOfWorkHelper name imported into
#          flexicon.code.transaction / flexicon.code.undoable_operation with a
#          fake double so they never touch a real LcmCache (the real
#          SIL.LCModel.Infrastructure CLR namespace does not support
#          attribute assignment, so it cannot be patched directly). Written
#          for the write-path-transactions B1/B3 rewrite (issues #233, #234).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import contextlib
import pytest
from unittest.mock import MagicMock, Mock, call, patch


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


class _FakeActionHandler:
    """
    Minimal ``IActionHandler`` double exposing a real, mutable ``CurrentDepth``
    int -- unlike a bare ``Mock()``, ``> 0`` comparisons work directly on it.

    ``CanUndo``/``CanRedo`` are exposed for the B3 (Undo/Redo) tests
    elsewhere; not every test here needs them.
    """

    def __init__(self, current_depth=0):
        self.CurrentDepth = current_depth
        self._can_undo = False
        self._can_redo = False
        self.undo_calls = 0
        self.redo_calls = 0

    def CanUndo(self):
        return self._can_undo

    def CanRedo(self):
        return self._can_redo

    def Undo(self):
        self.undo_calls += 1

    def Redo(self):
        self.redo_calls += 1


class _FakeUndoableUnitOfWorkHelper:
    """
    Stand-in for ``SIL.LCModel.Infrastructure.UndoableUnitOfWorkHelper``.

    Records constructor args and ``RollBack``/``Dispose`` activity so tests
    can assert on the join-vs-open decision and the rollback flag without a
    live ``LcmCache``. Mimics the two real-world facts this rewrite depends
    on:

      * the constructor "begins the undo task" -- here, simply bumps the
        fake action handler's ``CurrentDepth`` to 1 so a nested
        ``_NestingAwareTransaction``/``_FLExUndoableOperation`` sees an
        already-open UnitOfWork and joins instead of opening a second one;
      * ``RollBack`` defaults to True (``UnitOfWorkHelper.cs:31``) and
        ``Dispose()`` resets the depth back to 0 (approximating
        ``EndUndoTask``/``Rollback(0)``, both of which leave the FSM at
        ``ReadyForBeginTask``).

    ``instances`` is a class-level list of every instance constructed during
    a test; tests read and then clear it.
    """

    instances = []

    def __init__(self, action_handler, undo_text, redo_text):
        self.action_handler = action_handler
        self.undo_text = undo_text
        self.redo_text = redo_text
        self.RollBack = True  # ctor default (UnitOfWorkHelper.cs:31)
        self.disposed = False
        self.rollback_value_at_dispose = None
        type(self).instances.append(self)
        self.action_handler.CurrentDepth = 1

    def Dispose(self):
        self.disposed = True
        self.rollback_value_at_dispose = self.RollBack
        self.action_handler.CurrentDepth = 0


def _make_phase2_project(current_depth=0):
    """
    Phase 2 project (_undoable=True) with a real action-handler double at
    ``project.project.ActionHandlerAccessor`` -- the exact attribute path
    ``_NestingAwareTransaction``/``_FLExUndoableOperation`` read.
    """
    project = Mock()
    project.writeEnabled = True
    project._undoable = True
    project.project = Mock()
    project.project.ActionHandlerAccessor = _FakeActionHandler(current_depth)
    # Legacy Phase 1 escape hatch some shared helpers still reference.
    project.Transaction = Mock(
        side_effect=lambda label="transaction": contextlib.nullcontext()
    )
    return project


@pytest.fixture(autouse=True)
def _reset_fake_helper_instances():
    """Ensure _FakeUndoableUnitOfWorkHelper.instances never leaks across tests."""
    _FakeUndoableUnitOfWorkHelper.instances = []
    yield
    _FakeUndoableUnitOfWorkHelper.instances = []


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
# Phase 2: join-vs-open on liblcm's own CurrentDepth (B1 rewrite)
# ---------------------------------------------------------------------------

class TestPhase2JoinOrOpen:
    """
    PHASE 2: regression lock for the B1 rewrite of _NestingAwareTransaction
    onto UndoableUnitOfWorkHelper.

    Verifies:
    - CurrentDepth == 0  -> a new UndoableUnitOfWorkHelper is opened
    - CurrentDepth > 0   -> join (no second helper constructed)
    - RollBack is cleared (False) on a clean exit, left True (rolled back)
      on an exception
    - the helper ctor is always called with BOTH undo and redo text
      (regression lock for #233 -- the one-argument BeginUndoTask call can
      no longer occur, because there is no BeginUndoTask call at all here)
    - no local depth counter exists anywhere (there is nothing named
      `_transaction_depth` left to leak -- #234 dies by construction)
    """

    @patch(
        "flexicon.code.transaction.UndoableUnitOfWorkHelper",
        _FakeUndoableUnitOfWorkHelper,
    )
    def test_outermost_opens_new_unit_of_work(self):
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project(current_depth=0)
        action_handler = project.project.ActionHandlerAccessor

        with _NestingAwareTransaction(project, "outer"):
            assert len(_FakeUndoableUnitOfWorkHelper.instances) == 1
            assert action_handler.CurrentDepth == 1  # ctor "began the task"

        helper = _FakeUndoableUnitOfWorkHelper.instances[0]
        assert helper.disposed is True
        assert helper.rollback_value_at_dispose is False  # cleared on clean exit
        assert action_handler.CurrentDepth == 0  # Dispose() closed it

    @patch(
        "flexicon.code.transaction.UndoableUnitOfWorkHelper",
        _FakeUndoableUnitOfWorkHelper,
    )
    def test_ctor_called_with_both_undo_and_redo_text(self):
        """
        Regression lock for #233: the helper must be constructed with the
        action handler AND both undo/redo strings -- never a single string.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project(current_depth=0)

        with _NestingAwareTransaction(project, "Create entry 'run'"):
            pass

        helper = _FakeUndoableUnitOfWorkHelper.instances[0]
        assert helper.undo_text == "Create entry 'run'"
        assert helper.redo_text == "Create entry 'run'"

    @patch(
        "flexicon.code.transaction.UndoableUnitOfWorkHelper",
        _FakeUndoableUnitOfWorkHelper,
    )
    def test_nested_phase2_joins_without_opening_second_helper(self):
        """
        A second _NestingAwareTransaction entered while CurrentDepth > 0
        (i.e. the outer block's helper already bumped it) must NOT
        construct a second UndoableUnitOfWorkHelper.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project(current_depth=0)

        with _NestingAwareTransaction(project, "outer"):
            inner_ran = []
            with _NestingAwareTransaction(project, "inner"):
                inner_ran.append(True)
            assert inner_ran == [True]

        # Exactly one helper constructed (for the outer block only).
        assert len(_FakeUndoableUnitOfWorkHelper.instances) == 1

    @patch(
        "flexicon.code.transaction.UndoableUnitOfWorkHelper",
        _FakeUndoableUnitOfWorkHelper,
    )
    def test_rollback_flag_set_true_on_exception(self):
        """
        An exception inside the outermost block must leave RollBack True
        (the ctor default) at Dispose() time -- i.e. NOT cleared -- so
        liblcm's Dispose() rolls back rather than committing.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project(current_depth=0)

        with pytest.raises(RuntimeError, match="boom"):
            with _NestingAwareTransaction(project, "outer-raises"):
                raise RuntimeError("boom")

        helper = _FakeUndoableUnitOfWorkHelper.instances[0]
        assert helper.disposed is True
        assert helper.rollback_value_at_dispose is True

    @patch(
        "flexicon.code.transaction.UndoableUnitOfWorkHelper",
        _FakeUndoableUnitOfWorkHelper,
    )
    def test_nested_inner_exception_still_disposes_outer_with_rollback(self):
        """
        When the (joined, no-op) inner block raises, the outer helper must
        still see the exception at its own __exit__ and roll back.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project(current_depth=0)

        with pytest.raises(RuntimeError, match="inner boom"):
            with _NestingAwareTransaction(project, "outer"):
                with _NestingAwareTransaction(project, "inner"):
                    raise RuntimeError("inner boom")

        assert len(_FakeUndoableUnitOfWorkHelper.instances) == 1
        helper = _FakeUndoableUnitOfWorkHelper.instances[0]
        assert helper.disposed is True
        assert helper.rollback_value_at_dispose is True

    @patch(
        "flexicon.code.transaction.UndoableUnitOfWorkHelper",
        _FakeUndoableUnitOfWorkHelper,
    )
    def test_joins_a_unit_of_work_opened_by_something_else(self):
        """
        CurrentDepth is LCM's own state, so _NestingAwareTransaction must
        join a UnitOfWork opened by ANY caller -- not just one it opened
        itself. Simulate that by constructing the project with
        current_depth=1 directly (as if some other code already opened a
        task) and confirm no helper is constructed.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project = _make_phase2_project(current_depth=1)

        with _NestingAwareTransaction(project, "outer"):
            pass

        assert len(_FakeUndoableUnitOfWorkHelper.instances) == 0

    def test_no_local_transaction_depth_attribute_referenced_in_source(self):
        """
        #234 dies by construction: transaction.py must never set or read a
        `_transaction_depth` attribute on the project. (A runtime probe via
        `hasattr(project, ...)` on a bare `Mock()` is not meaningful here --
        Mock auto-vivifies any attribute name on access -- so this checks
        the source directly, mirroring the pattern used elsewhere in this
        suite, e.g. `tests/test_transaction_honesty.py`.)
        """
        import pathlib

        source = (
            pathlib.Path(__file__).resolve().parent.parent.parent
            / "flexicon"
            / "code"
            / "transaction.py"
        ).read_text(encoding="utf-8")

        assert "project._transaction_depth" not in source
        assert "self._transaction_depth" not in source


# ---------------------------------------------------------------------------
# Phase 1 nesting: independent rollback points
# ---------------------------------------------------------------------------

class TestPhase1Nesting:
    """
    Phase 1 nesting is allowed and each block gets its own mark.
    Phase 1 never opens an LCM undo task at all (the session-long
    non-undoable envelope is opened once at OpenProject()), so there is no
    LCM-level nesting concern to guard against in this mode.
    """

    def test_phase1_nested_enters_and_exits_cleanly(self):
        """
        Entering two nested _NestingAwareTransaction blocks (Phase 1)
        must enter and exit without error at any depth.
        """
        from flexlibs2.code.transaction import _NestingAwareTransaction

        project, mark_mock, rollback_mock = _make_phase1_project()

        with _NestingAwareTransaction(project, "outer"):
            with _NestingAwareTransaction(project, "inner"):
                pass

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


# ---------------------------------------------------------------------------
# _FLExUndoableOperation (FLExProject.UndoableOperation()) -- same join/open
# idiom, exercised directly. Regression lock for #233 at this entry point too.
# ---------------------------------------------------------------------------

class TestFLExUndoableOperation:
    """
    Direct coverage of undoable_operation._FLExUndoableOperation, the public
    FLExProject.UndoableOperation() context manager. Before B1 this called
    self._begin_undo_fn(self._label) with a single argument against liblcm's
    two-argument BeginUndoTask(String, String) -- issue #233. It now
    constructs UndoableUnitOfWorkHelper directly (or joins), the same as
    _NestingAwareTransaction.
    """

    def _make_project(self, current_depth=0, write_enabled=True, undoable=True):
        project = Mock()
        project.writeEnabled = write_enabled
        project._undoable = undoable
        project.project = Mock()
        project.project.ActionHandlerAccessor = _FakeActionHandler(current_depth)
        return project

    def test_raises_if_not_write_enabled(self):
        from flexlibs2.code.undoable_operation import _FLExUndoableOperation
        from flexlibs2.code.FLExProject import FP_ReadOnlyError

        project = self._make_project(write_enabled=False)
        op = _FLExUndoableOperation(project, "label")

        with pytest.raises(FP_ReadOnlyError):
            with op:
                pass

    def test_raises_if_not_undoable(self):
        from flexlibs2.code.undoable_operation import _FLExUndoableOperation
        from flexlibs2.code.FLExProject import FP_TransactionError

        project = self._make_project(undoable=False)
        op = _FLExUndoableOperation(project, "label")

        with pytest.raises(FP_TransactionError):
            with op:
                pass

    @patch(
        "flexicon.code.undoable_operation.UndoableUnitOfWorkHelper",
        _FakeUndoableUnitOfWorkHelper,
    )
    def test_opens_helper_with_both_undo_and_redo_text(self):
        """Regression lock for #233 at the UndoableOperation() entry point."""
        from flexlibs2.code.undoable_operation import _FLExUndoableOperation

        project = self._make_project(current_depth=0)

        with _FLExUndoableOperation(project, "Add entry 'run'"):
            pass

        helper = _FakeUndoableUnitOfWorkHelper.instances[0]
        assert helper.undo_text == "Add entry 'run'"
        assert helper.redo_text == "Add entry 'run'"
        assert helper.disposed is True
        assert helper.rollback_value_at_dispose is False

    @patch(
        "flexicon.code.undoable_operation.UndoableUnitOfWorkHelper",
        _FakeUndoableUnitOfWorkHelper,
    )
    def test_joins_when_current_depth_positive(self):
        from flexlibs2.code.undoable_operation import _FLExUndoableOperation

        project = self._make_project(current_depth=1)

        with _FLExUndoableOperation(project, "inner"):
            pass

        assert len(_FakeUndoableUnitOfWorkHelper.instances) == 0

    @patch(
        "flexicon.code.undoable_operation.UndoableUnitOfWorkHelper",
        _FakeUndoableUnitOfWorkHelper,
    )
    def test_rollback_on_exception(self):
        from flexlibs2.code.undoable_operation import _FLExUndoableOperation

        project = self._make_project(current_depth=0)

        with pytest.raises(RuntimeError, match="boom"):
            with _FLExUndoableOperation(project, "label"):
                raise RuntimeError("boom")

        helper = _FakeUndoableUnitOfWorkHelper.instances[0]
        assert helper.rollback_value_at_dispose is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
