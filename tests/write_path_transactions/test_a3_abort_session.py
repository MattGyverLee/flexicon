#
#   test_a3_abort_session.py
#
#   Class: TestA3AbortSession
#          Offline guard for task A3 (specs/write-path-transactions/tasks.md):
#          `FLExProject.AbortSession()` exposes liblcm's one real revert
#          primitive, `IActionHandler.Rollback(0)`.
#
#          The properties worth pinning are all consequences of the O2 catch
#          (spec.md O2, reviews/cycle2-explore-liblcm-facts.md F5c), none of
#          which are visible from the method signature:
#
#          1. `Rollback` requires an open task and throws otherwise
#             (UndoStack.cs:712-713), so a no-task call must return False
#             rather than let InvalidOperationException escape.
#          2. `Rollback` leaves the FSM in ReadyForBeginTask
#             (UndoStack.cs:724) -- it TERMINATES the open task. Under
#             undoable=False the session envelope must therefore be reopened,
#             or CloseProject()'s EndNonUndoableTask() has nothing to end.
#          3. Under undoable=True an open unit belongs to an
#             UndoableUnitOfWorkHelper; rolling back underneath it would make
#             its Dispose() raise. AbortSession must refuse, not comply.
#
#          No FieldWorks, no pythonnet, no live project: every test binds the
#          real `FLExProject.AbortSession` body onto a strict plain-Python
#          double that models the UndoStack state machine. Nothing here
#          writes to the LCM.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

"""Offline contract tests for `FLExProject.AbortSession()` (task A3)."""

import pytest


# ---------------------------------------------------------------------------
# Doubles -- model the liblcm UndoStack FSM, not a convenient approximation
# ---------------------------------------------------------------------------
#
# Facts modeled, each traceable to a source line cited in
# specs/write-path-transactions/reviews/cycle2-explore-liblcm-facts.md:
#
#   * CurrentDepth == 1 iff CurrentProcessingState is ProcessingDataChanges,
#     0 otherwise; never 2+ (F2 / UndoStack.cs:731-734). Exposed read-only,
#     so production code that tried to assign it would raise.
#   * Rollback(nDepth) requires an open task or throws
#     InvalidOperationException("Rollback not supported in the current
#     state.") (F5c / UndoStack.cs:712-713), ignores nDepth entirely
#     (UndoStack.cs:700), and sets the state back to ReadyForBeginTask
#     (UndoStack.cs:724) -- it ends the task rather than emptying it.
#   * BeginNonUndoableTask() refuses while data changes are in progress
#     (UndoStack.cs:259, CheckNotProcessingDataChanges) -- the same guard
#     BeginUndoTask uses.


class RollbackStateError(RuntimeError):
    """Stand-in for System.InvalidOperationException from the LCM."""


class FsmActionHandler:
    """Plain-Python double for the parts of IActionHandler that A3 touches."""

    def __init__(self, depth=0):
        self._current_depth = depth
        self.rollback_calls = []          # nDepth args actually passed
        self.begin_non_undoable_calls = 0
        self.end_non_undoable_calls = 0

    @property
    def CurrentDepth(self):
        """Get-only on the real type (UndoStack.cs:731-734)."""
        return self._current_depth

    def Rollback(self, nDepth):
        if self._current_depth == 0:
            raise RollbackStateError("Rollback not supported in the current state.")
        self.rollback_calls.append(nDepth)
        # UndoStack.cs:724 -- back to ReadyForBeginTask; the task is GONE.
        self._current_depth = 0

    def BeginNonUndoableTask(self):
        if self._current_depth > 0:
            raise RollbackStateError("Nested tasks are not supported.")
        self.begin_non_undoable_calls += 1
        self._current_depth = 1

    def EndNonUndoableTask(self):
        if self._current_depth == 0:
            raise RollbackStateError("EndNonUndoableTask with no open task.")
        self.end_non_undoable_calls += 1
        self._current_depth = 0


class FsmCache:
    """
    Double for LcmCache. `MainCacheAccessor` and `ActionHandlerAccessor` are
    the same handler object here, which is faithful: OpenProject() drives the
    envelope through MainCacheAccessor while Undo()/Redo() read
    ActionHandlerAccessor, and in liblcm both reach the same active stack.

    Strict on purpose -- no auto-vivification, so any attribute AbortSession()
    touches that is not modeled raises AttributeError instead of silently
    passing.
    """

    def __init__(self, action_handler):
        self.ActionHandlerAccessor = action_handler
        self.MainCacheAccessor = action_handler


class FakeFLExProject:
    """The three attributes `AbortSession()` reads, and nothing else."""

    def __init__(self, writeEnabled=True, undoable=False, depth=1):
        self.writeEnabled = writeEnabled
        self._undoable = undoable
        self.handler = FsmActionHandler(depth=depth)
        self.project = FsmCache(self.handler)


def _abort(project):
    """Run the REAL method body against the double (never a re-implementation)."""
    from flexicon.code.FLExProject import FLExProject

    return FLExProject.AbortSession(project)


def _exceptions():
    from flexicon.code import exceptions

    return exceptions


# ---------------------------------------------------------------------------


class TestGuards:
    """Preconditions that must be refused before anything is rolled back."""

    def test_read_only_project_raises_read_only_error(self):
        exc = _exceptions()
        project = FakeFLExProject(writeEnabled=False)

        with pytest.raises(exc.FP_ReadOnlyError):
            _abort(project)

        assert project.handler.rollback_calls == []

    def test_no_open_task_returns_false_without_calling_rollback(self):
        """
        Rollback throws when nothing is open (UndoStack.cs:712-713). The
        CurrentDepth == 0 check must turn that into an honest False instead
        of letting the raw LCM exception escape -- and must not call Rollback
        at all, since calling it is precisely what would throw.
        """
        project = FakeFLExProject(depth=0)

        assert _abort(project) is False
        assert project.handler.rollback_calls == []
        assert project.handler.begin_non_undoable_calls == 0

    def test_undoable_mode_with_open_unit_refuses_and_does_not_roll_back(self):
        """
        In undoable=True an open unit is owned by an UndoableUnitOfWorkHelper.
        Rolling back underneath it would leave its Dispose() to act on a FSM
        already in ReadyForBeginTask, raising a second exception from the
        block's exit and masking the first. Refusing must leave the unit
        untouched, so the enclosing block still rolls itself back normally.
        """
        exc = _exceptions()
        project = FakeFLExProject(undoable=True, depth=1)

        with pytest.raises(exc.FP_TransactionError):
            _abort(project)

        assert project.handler.rollback_calls == []
        assert project.handler.CurrentDepth == 1  # still owned by the helper

    def test_undoable_mode_with_nothing_open_returns_false(self):
        """Between operations in undoable=True there is no session envelope,
        so there is nothing to abort -- False, not a raise."""
        project = FakeFLExProject(undoable=True, depth=0)

        assert _abort(project) is False
        assert project.handler.rollback_calls == []


class TestRollbackPath:
    """The undoable=False path: the mode A3 exists for."""

    def test_rolls_back_and_reports_true(self):
        project = FakeFLExProject(undoable=False, depth=1)

        assert _abort(project) is True
        assert len(project.handler.rollback_calls) == 1

    def test_passes_zero_as_ndepth(self):
        """
        nDepth is "[Not used.]" (UndoStack.cs:700) and 0 is what liblcm's own
        UnitOfWorkHelper.RollBackChanges() passes (UnitOfWorkHelper.cs:135-138).
        Pinned so nobody later invents a partial-rollback depth argument that
        liblcm would silently ignore.
        """
        project = FakeFLExProject(undoable=False, depth=1)
        _abort(project)

        assert project.handler.rollback_calls == [0]

    def test_reopens_the_session_envelope_after_rollback(self):
        """
        THE O2 CATCH. Rollback leaves the FSM in ReadyForBeginTask
        (UndoStack.cs:724) -- the envelope opened at OpenProject() is gone,
        not merely emptied. Without a reopen, CloseProject()'s
        EndNonUndoableTask() would have no task to end.
        """
        project = FakeFLExProject(undoable=False, depth=1)

        assert _abort(project) is True
        assert project.handler.begin_non_undoable_calls == 1
        assert project.handler.CurrentDepth == 1

    def test_close_project_envelope_still_balances_after_abort(self):
        """
        End-to-end consequence of the reopen: the EndNonUndoableTask() that
        CloseProject() issues must still succeed after an abort. This is the
        property test_reopens_... protects, asserted from the caller's side.
        """
        project = FakeFLExProject(undoable=False, depth=1)
        _abort(project)

        project.project.MainCacheAccessor.EndNonUndoableTask()  # must not raise
        assert project.handler.end_non_undoable_calls == 1
        assert project.handler.CurrentDepth == 0

    def test_abort_is_repeatable(self):
        """Non-terminal: because the envelope is reopened, a second abort in
        the same session finds an open task and works exactly like the first."""
        project = FakeFLExProject(undoable=False, depth=1)

        assert _abort(project) is True
        assert _abort(project) is True
        assert project.handler.rollback_calls == [0, 0]
        assert project.handler.begin_non_undoable_calls == 2


class TestFailureMapping:
    """LCM exceptions must surface as flexicon exceptions, never raw."""

    def test_unexpected_rollback_failure_becomes_transaction_error(self):
        exc = _exceptions()
        project = FakeFLExProject(undoable=False, depth=1)

        def _boom(nDepth):
            raise RollbackStateError("Rollback not supported in the current state.")

        project.handler.Rollback = _boom

        with pytest.raises(exc.FP_TransactionError):
            _abort(project)

        # The envelope was never re-opened, because nothing was rolled back.
        assert project.handler.begin_non_undoable_calls == 0

    def test_rollback_failure_does_not_leave_a_partial_reopen(self):
        """A failed rollback must not be followed by a BeginNonUndoableTask()
        that would open a SECOND envelope on top of the still-open one."""
        project = FakeFLExProject(undoable=False, depth=1)
        exc = _exceptions()

        def _boom(nDepth):
            raise RollbackStateError("boom")

        project.handler.Rollback = _boom

        with pytest.raises(exc.FP_TransactionError):
            _abort(project)

        assert project.handler.CurrentDepth == 1  # untouched


class TestApiSurface:
    """Shape checks that do not need a project at all."""

    def test_method_exists_on_flexproject(self):
        from flexicon.code.FLExProject import FLExProject

        assert callable(getattr(FLExProject, "AbortSession", None))

    def test_docstring_states_the_o2_catch(self):
        """
        Task A3 requires the O2 catch be *documented*, not merely handled:
        a caller reading the docstring must learn that Rollback ends the task
        and that the envelope is reopened. A silent fix is a spec miss.
        """
        from flexicon.code.FLExProject import FLExProject

        doc = FLExProject.AbortSession.__doc__ or ""
        assert "ReadyForBeginTask" in doc
        assert "BeginNonUndoableTask" in doc

    def test_docstring_does_not_promise_partial_rollback(self):
        """`nDepth` is ignored by liblcm; the docstring must not imply the
        method can revert a selected subset (constitution V)."""
        from flexicon.code.FLExProject import FLExProject

        doc = FLExProject.AbortSession.__doc__ or ""
        assert "no partial rollback" in doc.lower()
