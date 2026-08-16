#
#   test_b1t_action_handler_double.py
#
#   Class: TestB1tActionHandlerDouble
#          Independent verification suite for the B1 (_NestingAwareTransaction /
#          _FLExUndoableOperation) and B3 (Undo()/Redo()) rewrite, cycle 3.
#
#          Written by the Verification Agent as an INDEPENDENT check -- it does
#          not import or reuse fixtures from
#          tests/operations/test_transaction_rollback.py or tests/test_undo_redo.py
#          (the programmer's own tests), and builds its own action-handler and
#          UndoableUnitOfWorkHelper doubles from the liblcm source facts in
#          specs/write-path-transactions/reviews/cycle2-explore-liblcm-facts.md
#          and specs/write-path-transactions/issues/createfield-always-raises.md,
#          not from the programmer's report.
#
#          No live FLEx project is opened and no live LCM write is executed
#          anywhere in this file (per the cycle-3 ABSOLUTE CONSTRAINT) -- every
#          test below patches flexicon.code.transaction.UndoableUnitOfWorkHelper
#          / flexicon.code.undoable_operation.UndoableUnitOfWorkHelper with the
#          FaithfulUndoableUnitOfWorkHelper double defined here, which itself
#          only manipulates a plain-Python FaithfulActionHandler double.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest
from unittest.mock import Mock, patch


# ---------------------------------------------------------------------------
# FaithfulActionHandler -- models the REAL liblcm IActionHandler state machine
# ---------------------------------------------------------------------------
#
# Facts modeled, each traceable to a specific liblcm source line cited in
# specs/write-path-transactions/reviews/cycle2-explore-liblcm-facts.md (F1, F2)
# and specs/write-path-transactions/issues/createfield-always-raises.md:
#
#   * CurrentDepth is 1 iff a data-changing task (undo or non-undoable) is
#     open, 0 otherwise (UndoStack.cs:731-734 / createfield-always-raises.md
#     link 2). It is a get-only property on the real interface -- this double
#     therefore does NOT expose a settable public attribute a caller could
#     assign directly; it is only ever mutated by BeginUndoTask/EndUndoTask/
#     Rollback below, mirroring the real read-only surface.
#   * A second BeginUndoTask() while CurrentDepth > 0 does not merely refuse:
#     UndoStack.cs:209-216 calls Rollback(0) FIRST -- discarding the
#     already-open unit's changes -- and only THEN raises
#     InvalidOperationException("Nested tasks are not supported."). This
#     double reproduces that exact ordering (destroy, then throw), not just
#     the throw.
#   * Rollback(int nDepth) (UnitOfWorkHelper.cs:135-138 calls
#     m_actionHandler.Rollback(0) verbatim) discards the current bundle and
#     resets CurrentDepth to 0. It requires an open task (CurrentDepth == 1)
#     or raises, matching UndoStack.cs:712-713.


class FaithfulActionHandler:
    """
    Plain-Python double for SIL.LCModel.Infrastructure IActionHandler.

    CurrentDepth is exposed as a read-only property (backed by a private
    attribute) so any implementation code that tries to WRITE CurrentDepth
    directly (instead of going through BeginUndoTask/EndUndoTask/Rollback)
    raises AttributeError, matching the real type's get-only auto-property
    (UndoStack.cs:731-734).
    """

    def __init__(self):
        self._current_depth = 0
        self.begin_undo_calls = []       # list of (undo_text, redo_text)
        self.end_undo_calls = 0
        self.rollback_calls = []         # list of nDepth args passed
        self.destructive_rollback_count = 0  # rollbacks fired by a REJECTED
        # second BeginUndoTask (the F1 destructive path), tracked separately
        # so tests can assert that path was never hit by production code
        # even though both paths ultimately call the same self.Rollback().
        self._can_undo = False
        self._can_redo = False
        self.undo_calls = 0
        self.redo_calls = 0

    @property
    def CurrentDepth(self):
        return self._current_depth

    def BeginUndoTask(self, undo_text, redo_text):
        """
        Faithful to UndoStack.cs:187-216 (2-arg IActionHandler signature
        confirmed in tests/contract/snapshots/liblcm_baseline.json
        method_signatures.BeginUndoTask == [["String", "String"]]).
        """
        if self._current_depth > 0:
            # F1: destructive-then-throw. Roll back the ALREADY-OPEN unit's
            # changes first (discarding them), reset state, THEN raise.
            self.destructive_rollback_count += 1
            self.Rollback(0)
            raise RuntimeError("Nested tasks are not supported.")
        self.begin_undo_calls.append((undo_text, redo_text))
        self._current_depth = 1

    def EndUndoTask(self):
        if self._current_depth == 0:
            raise RuntimeError("EndUndoTask called with no open task.")
        self.end_undo_calls += 1
        self._current_depth = 0

    def Rollback(self, nDepth):
        """
        UnitOfWorkHelper.cs:135-138 always calls this with 0
        (m_actionHandler.Rollback(0)); UndoStack.cs:705-713 requires an
        open task or raises. nDepth is documented "[Not used.]" in source
        (cycle2-explore-liblcm-facts.md F5c) -- recorded here for the
        argument assertion but not otherwise interpreted.
        """
        if self._current_depth == 0:
            raise RuntimeError("Rollback not supported in the current state.")
        self.rollback_calls.append(nDepth)
        self._current_depth = 0

    def CanUndo(self):
        return self._can_undo

    def CanRedo(self):
        return self._can_redo

    def Undo(self):
        if not self._can_undo:
            raise RuntimeError("Undo() called with CanUndo() False.")
        self.undo_calls += 1

    def Redo(self):
        if not self._can_redo:
            raise RuntimeError("Redo() called with CanRedo() False.")
        self.redo_calls += 1


class FaithfulUndoableUnitOfWorkHelper:
    """
    Double for SIL.LCModel.Infrastructure.UndoableUnitOfWorkHelper that
    routes EVERY state change through a FaithfulActionHandler instance,
    rather than just flipping an internal flag -- so a bug in
    transaction.py/undoable_operation.py that bypassed the join check would
    manifest as a second BeginUndoTask call against the SAME action handler
    and would be caught by the destructive-rollback accounting above, not
    silently absorbed by the double.

    Constructor ((IActionHandler, String, String)) and RollBack semantics
    (defaults True per UnitOfWorkHelper.cs:31; commit calls EndUndoTask,
    rollback calls Rollback(0)) match
    tests/contract/snapshots/liblcm_baseline.json's UndoableUnitOfWorkHelper
    entry (constructors, reflected_properties.RollBack).

    ROLLBACK ACCESS SHAPE (corrected after live verification, task A3).
    `RollBack` is `{private get; set;}` in C#, and pythonnet does NOT
    synthesize a Python property when the getter is private -- it exposes
    only the raw `set_RollBack` accessor. Confirmed live on the Target
    sandbox: `hasattr(helper, "RollBack")` is False and
    `dir(UndoableUnitOfWorkHelper)` contains `set_RollBack`/`RollBackChanges`
    but no `RollBack`.

    The consequence is the whole reason this double was wrong before:
    `helper.RollBack = False` does not raise on the real type either. It
    silently lands as a plain Python attribute on the wrapper while the .NET
    field keeps its constructor default of True -- so Dispose() rolled back
    EVERY unit of work, clean ones included, and `undoable=True` mode lost
    every write it made. The old double modelled `RollBack` assignment as
    working, which is exactly why an offline suite of 30 tests passed against
    code that destroyed all data on a live LCM.

    This double therefore refuses the assignment form outright: production
    code must call `set_RollBack(...)`. That makes the bug impossible to
    reintroduce without turning this suite red.
    """

    instances = []

    def __init__(self, action_handler, undo_text, redo_text):
        if not isinstance(undo_text, str) or not isinstance(redo_text, str):
            raise TypeError(
                "UndoableUnitOfWorkHelper ctor requires (IActionHandler, "
                "String undoText, String redoText) -- got "
                f"undo_text={undo_text!r}, redo_text={redo_text!r}"
            )
        self.action_handler = action_handler
        self.undo_text = undo_text
        self.redo_text = redo_text
        action_handler.BeginUndoTask(undo_text, redo_text)  # ctor opens the task
        self._rollback = True  # UnitOfWorkHelper.cs:31 default
        self._disposed = False
        type(self).instances.append(self)

    def __setattr__(self, name, value):
        # `helper.RollBack = x` must never be how production code sets this.
        # On the real pythonnet wrapper that assignment silently does nothing
        # to .NET (see class docstring); here it raises, which is the only
        # way an offline suite can catch the mistake at all.
        if name == "RollBack":
            raise AttributeError(
                "pythonnet exposes no settable `RollBack` property on "
                "UndoableUnitOfWorkHelper (the C# getter is private, so only "
                "`set_RollBack` is surfaced). Assigning it silently leaves "
                "the real flag True and rolls back every clean UnitOfWork -- "
                "call set_RollBack(...) instead."
            )
        object.__setattr__(self, name, value)

    def set_RollBack(self, value):
        """The accessor pythonnet actually exposes (verified live, A3)."""
        object.__setattr__(self, "_rollback", value)

    def Dispose(self):
        if self._disposed:
            return
        self._disposed = True
        if self._rollback:
            self.action_handler.Rollback(0)
        else:
            self.action_handler.EndUndoTask()


@pytest.fixture(autouse=True)
def _reset_helper_instances():
    FaithfulUndoableUnitOfWorkHelper.instances = []
    yield
    FaithfulUndoableUnitOfWorkHelper.instances = []


def _phase2_project(action_handler=None):
    """Phase 2 (_undoable=True) project double, own construction -- not
    shared with tests/operations/test_transaction_rollback.py's helpers."""
    ah = action_handler if action_handler is not None else FaithfulActionHandler()
    project = Mock()
    project.writeEnabled = True
    project._undoable = True
    project.project = Mock()
    project.project.ActionHandlerAccessor = ah
    return project, ah


def _phase1_project():
    """Phase 1 (_undoable=False) project double."""
    project = Mock()
    project.writeEnabled = True
    project._undoable = False
    calls = []

    def _transaction(label="transaction"):
        import contextlib

        calls.append(label)
        return contextlib.nullcontext()

    project.Transaction = Mock(side_effect=_transaction)
    return project, calls


_PATCH_TXN = patch(
    "flexicon.code.transaction.UndoableUnitOfWorkHelper",
    FaithfulUndoableUnitOfWorkHelper,
)
_PATCH_UOP = patch(
    "flexicon.code.undoable_operation.UndoableUnitOfWorkHelper",
    FaithfulUndoableUnitOfWorkHelper,
)


# ---------------------------------------------------------------------------
# 0. Sanity: the double itself faithfully reproduces the destructive
#    double-begin path described by F1 -- exercised directly, with NO
#    production code involved, to prove the double is not a rubber stamp.
# ---------------------------------------------------------------------------

class TestDoubleFidelity:
    def test_double_reproduces_destructive_rollback_then_throw(self):
        ah = FaithfulActionHandler()
        ah.BeginUndoTask("outer", "outer")
        assert ah.CurrentDepth == 1

        with pytest.raises(RuntimeError, match="Nested tasks are not supported"):
            ah.BeginUndoTask("inner", "inner")

        # The destructive path fired: the open unit's "changes" were
        # discarded via Rollback(0) BEFORE the throw, not merely rejected.
        assert ah.destructive_rollback_count == 1
        assert ah.rollback_calls == [0]
        # And the FSM was reset -- a fresh BeginUndoTask now succeeds.
        assert ah.CurrentDepth == 0
        ah.BeginUndoTask("third", "third")
        assert ah.CurrentDepth == 1

    def test_double_rollback_requires_open_task(self):
        ah = FaithfulActionHandler()
        with pytest.raises(RuntimeError, match="not supported in the current state"):
            ah.Rollback(0)

    def test_double_rejects_rollback_property_assignment(self):
        """
        Regression guard for the A3 live finding. pythonnet surfaces no
        `RollBack` property (private C# getter), so `helper.RollBack = False`
        silently fails to reach .NET and leaves every clean UnitOfWork to be
        rolled back on Dispose(). The double refuses the form so the mistake
        cannot pass offline again.
        """
        ah = FaithfulActionHandler()
        helper = FaithfulUndoableUnitOfWorkHelper(ah, "label", "label")

        with pytest.raises(AttributeError, match="set_RollBack"):
            helper.RollBack = False

        # Reading is impossible too -- there is no getter of any kind.
        with pytest.raises(AttributeError):
            _ = helper.RollBack

    def test_double_accepts_the_set_rollback_accessor(self):
        """`set_RollBack` is the accessor pythonnet actually exposes."""
        ah = FaithfulActionHandler()
        helper = FaithfulUndoableUnitOfWorkHelper(ah, "label", "label")

        helper.set_RollBack(False)
        helper.Dispose()

        assert ah.rollback_calls == []      # committed, not rolled back
        assert ah.end_undo_calls == 1

    def test_source_never_assigns_the_rollback_property(self):
        """
        Source-level sweep. Neither transaction.py nor undoable_operation.py
        may contain a `.RollBack =` assignment: on a live LCM that form is a
        silent no-op that discards the block's writes. Only `set_RollBack(`
        reaches .NET.
        """
        import inspect
        import re

        from flexicon.code import transaction, undoable_operation

        pattern = re.compile(r"^\s*[^#]*\.RollBack\s*=", re.MULTILINE)

        for module in (transaction, undoable_operation):
            source = inspect.getsource(module)
            offenders = pattern.findall(source)
            assert not offenders, (
                f"{module.__name__} assigns .RollBack directly ({offenders!r}). "
                "pythonnet ignores that assignment -- use set_RollBack(...)."
            )
            assert "set_RollBack(" in source, (
                f"{module.__name__} never calls set_RollBack(), so its "
                "UnitOfWork can never commit."
            )


# ---------------------------------------------------------------------------
# 1. Nesting: inner _TransactionCM inside outer JOINS. Exactly one
#    BeginUndoTask total, ZERO Rollback calls anywhere.
# ---------------------------------------------------------------------------

class TestNestingJoins:
    def test_nested_transaction_cm_joins_single_begin_zero_rollback(self):
        from flexicon.code.transaction import _NestingAwareTransaction

        project, ah = _phase2_project()

        with _PATCH_TXN:
            with _NestingAwareTransaction(project, "outer op"):
                assert ah.CurrentDepth == 1
                with _NestingAwareTransaction(project, "inner op"):
                    assert ah.CurrentDepth == 1  # still just the outer's task
                assert ah.CurrentDepth == 1  # inner join did not close it

        assert ah.begin_undo_calls == [("outer op", "outer op")]
        assert ah.end_undo_calls == 1
        assert ah.rollback_calls == []
        assert ah.destructive_rollback_count == 0
        assert len(FaithfulUndoableUnitOfWorkHelper.instances) == 1

    def test_undoable_operation_nested_inside_transaction_cm_joins(self):
        """Cross-entry-point join: FLExProject.UndoableOperation() nested
        inside a _TransactionCM block (the mixed-caller case CurrentDepth
        is explicitly designed to support)."""
        from flexicon.code.transaction import _NestingAwareTransaction
        from flexicon.code.undoable_operation import _FLExUndoableOperation

        project, ah = _phase2_project()

        with _PATCH_TXN, _PATCH_UOP:
            with _NestingAwareTransaction(project, "outer"):
                with _FLExUndoableOperation(project, "inner"):
                    pass

        assert ah.begin_undo_calls == [("outer", "outer")]
        assert ah.rollback_calls == []
        assert ah.destructive_rollback_count == 0

    def test_triple_nesting_still_one_begin_zero_rollback(self):
        from flexicon.code.transaction import _NestingAwareTransaction

        project, ah = _phase2_project()

        with _PATCH_TXN:
            with _NestingAwareTransaction(project, "a"):
                with _NestingAwareTransaction(project, "b"):
                    with _NestingAwareTransaction(project, "c"):
                        pass

        assert len(ah.begin_undo_calls) == 1
        assert ah.rollback_calls == []
        assert ah.destructive_rollback_count == 0


# ---------------------------------------------------------------------------
# 2. Depth leak (#234 regression): exception inside inner AND inside outer
#    each leave CurrentDepth back at its starting value. `_transaction_depth`
#    must not exist as an ATTRIBUTE anywhere (absence, not merely zero).
# ---------------------------------------------------------------------------

class TestNoDepthLeak:
    def test_inner_exception_restores_starting_depth(self):
        from flexicon.code.transaction import _NestingAwareTransaction

        project, ah = _phase2_project()
        assert ah.CurrentDepth == 0

        with _PATCH_TXN:
            with pytest.raises(ValueError, match="inner blew up"):
                with _NestingAwareTransaction(project, "outer"):
                    with _NestingAwareTransaction(project, "inner"):
                        raise ValueError("inner blew up")

        assert ah.CurrentDepth == 0  # back to starting value

    def test_outer_exception_restores_starting_depth(self):
        from flexicon.code.transaction import _NestingAwareTransaction

        project, ah = _phase2_project()

        with _PATCH_TXN:
            with pytest.raises(ValueError, match="outer blew up"):
                with _NestingAwareTransaction(project, "outer"):
                    raise ValueError("outer blew up")

        assert ah.CurrentDepth == 0

    def test_depth_restored_across_repeated_use_after_exceptions(self):
        """Depth must not creep upward across repeated exception cycles --
        the exact #234 failure mode (a hand-rolled counter that only ever
        incremented on a raising __enter__)."""
        from flexicon.code.transaction import _NestingAwareTransaction

        project, ah = _phase2_project()

        with _PATCH_TXN:
            for i in range(5):
                with pytest.raises(RuntimeError):
                    with _NestingAwareTransaction(project, f"outer-{i}"):
                        with _NestingAwareTransaction(project, f"inner-{i}"):
                            raise RuntimeError(f"boom-{i}")
                assert ah.CurrentDepth == 0, f"leak detected after iteration {i}"

        assert ah.destructive_rollback_count == 0

    def test_no_transaction_depth_attribute_on_project_after_use(self):
        """
        Runtime-side check (not merely source-grep): after driving several
        nested/exception cycles, the project double must never have had
        `_transaction_depth` set on it. A bare Mock() would auto-vivify any
        attribute name on access, defeating this check, so this test uses a
        strict object that does NOT auto-vivify attributes.
        """
        from flexicon.code.transaction import _NestingAwareTransaction

        class _StrictProject:
            """A project stand-in that does NOT auto-vivify attributes,
            unlike unittest.mock.Mock, so hasattr() is meaningful."""

            def __init__(self, action_handler):
                self.writeEnabled = True
                self._undoable = True
                self.project = Mock()
                self.project.ActionHandlerAccessor = action_handler

        ah = FaithfulActionHandler()
        project = _StrictProject(ah)

        with _PATCH_TXN:
            with _NestingAwareTransaction(project, "outer"):
                with _NestingAwareTransaction(project, "inner"):
                    pass
            with pytest.raises(RuntimeError):
                with _NestingAwareTransaction(project, "outer2"):
                    raise RuntimeError("boom")

        assert not hasattr(project, "_transaction_depth")
        txn = _NestingAwareTransaction(project, "probe")
        assert not hasattr(txn, "_transaction_depth")

    def test_source_never_references_transaction_depth_attribute(self):
        """
        Independent re-derivation of the source-scan regression lock (this
        agent's own read of the file, not trusting the programmer's grep
        claim in cycle3-programmer-b1b3.md).
        """
        import pathlib

        source = (
            pathlib.Path(__file__).resolve().parent.parent
            / "flexicon"
            / "code"
            / "transaction.py"
        ).read_text(encoding="utf-8")

        assert "_transaction_depth" not in source, (
            "transaction.py must not reference _transaction_depth anywhere "
            "(attribute must be ABSENT, not merely zero -- issue #234)"
        )


# ---------------------------------------------------------------------------
# 3. Rollback: exception at outermost -> Rollback invoked. Clean exit ->
#    Rollback NOT invoked (EndUndoTask instead).
# ---------------------------------------------------------------------------

class TestRollbackInvocation:
    def test_exception_triggers_rollback_not_end_undo_task(self):
        from flexicon.code.transaction import _NestingAwareTransaction

        project, ah = _phase2_project()

        with _PATCH_TXN:
            with pytest.raises(KeyError):
                with _NestingAwareTransaction(project, "label"):
                    raise KeyError("boom")

        assert ah.rollback_calls == [0]
        assert ah.end_undo_calls == 0

    def test_clean_exit_triggers_end_undo_task_not_rollback(self):
        from flexicon.code.transaction import _NestingAwareTransaction

        project, ah = _phase2_project()

        with _PATCH_TXN:
            with _NestingAwareTransaction(project, "label"):
                pass

        assert ah.rollback_calls == []
        assert ah.end_undo_calls == 1

    def test_undoable_operation_exception_triggers_rollback(self):
        from flexicon.code.undoable_operation import _FLExUndoableOperation

        project, ah = _phase2_project()

        with _PATCH_UOP:
            with pytest.raises(KeyError):
                with _FLExUndoableOperation(project, "label"):
                    raise KeyError("boom")

        assert ah.rollback_calls == [0]
        assert ah.end_undo_calls == 0

    def test_undoable_operation_clean_exit_no_rollback(self):
        from flexicon.code.undoable_operation import _FLExUndoableOperation

        project, ah = _phase2_project()

        with _PATCH_UOP:
            with _FLExUndoableOperation(project, "label"):
                pass

        assert ah.rollback_calls == []
        assert ah.end_undo_calls == 1

    def test_inner_join_exception_still_rolls_back_via_outer(self):
        """A joined (no-op) inner block raising must still be observed by
        the OUTER helper's Dispose(), which does the actual Rollback."""
        from flexicon.code.transaction import _NestingAwareTransaction

        project, ah = _phase2_project()

        with _PATCH_TXN:
            with pytest.raises(RuntimeError):
                with _NestingAwareTransaction(project, "outer"):
                    with _NestingAwareTransaction(project, "inner"):
                        raise RuntimeError("inner boom")

        assert ah.rollback_calls == [0]
        assert ah.destructive_rollback_count == 0  # never hit the F1 path


# ---------------------------------------------------------------------------
# 4. BeginUndoTask arity (#233): the constructed helper always uses BOTH
#    undo and redo text, matching IActionHandler.BeginUndoTask(String,
#    String) per tests/contract/snapshots/liblcm_baseline.json.
# ---------------------------------------------------------------------------

class TestBeginUndoTaskArity:
    def test_arity_matches_baseline_contract(self):
        import json
        import pathlib

        baseline_path = (
            pathlib.Path(__file__).resolve().parent
            / "contract"
            / "snapshots"
            / "liblcm_baseline.json"
        )
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

        # Locate IActionHandler's BeginUndoTask signature list in the
        # baseline, independent of the top-level key layout (search, don't
        # assume a fixed path).
        found_sigs = None

        def _search(node):
            nonlocal found_sigs
            if found_sigs is not None:
                return
            if isinstance(node, dict):
                if (
                    "method_signatures" in node
                    and isinstance(node["method_signatures"], dict)
                    and "BeginUndoTask" in node["method_signatures"]
                    and "CanUndo" in node.get("method_signatures", {})
                ):
                    found_sigs = node["method_signatures"]["BeginUndoTask"]
                    return
                for v in node.values():
                    _search(v)
            elif isinstance(node, list):
                for v in node:
                    _search(v)

        _search(baseline)
        assert found_sigs is not None, "Could not locate IActionHandler.BeginUndoTask in baseline"
        assert ["String", "String"] in found_sigs, (
            f"Expected a (String, String) overload in baseline, got {found_sigs}"
        )

    def test_helper_always_constructed_with_two_strings(self):
        from flexicon.code.transaction import _NestingAwareTransaction

        project, ah = _phase2_project()

        with _PATCH_TXN:
            with _NestingAwareTransaction(project, "Create entry 'run'"):
                pass

        assert ah.begin_undo_calls == [("Create entry 'run'", "Create entry 'run'")]
        for undo_text, redo_text in ah.begin_undo_calls:
            assert isinstance(undo_text, str)
            assert isinstance(redo_text, str)

    def test_single_argument_begin_undo_task_would_be_rejected_by_double(self):
        """
        Belt-and-braces: confirm our own double would have caught the old
        #233 bug if it recurred -- calling BeginUndoTask with one arg raises
        TypeError (missing required positional argument), which is exactly
        the class of bug #233 was.
        """
        ah = FaithfulActionHandler()
        with pytest.raises(TypeError):
            ah.BeginUndoTask("only-one-arg")


# ---------------------------------------------------------------------------
# 5. undoable=False regression: still routes to project.Transaction(),
#    unchanged.
# ---------------------------------------------------------------------------

class TestPhase1Unchanged:
    def test_phase1_routes_to_project_transaction_regardless_of_nesting(self):
        from flexicon.code.transaction import _NestingAwareTransaction

        project, calls = _phase1_project()

        with _NestingAwareTransaction(project, "outer"):
            with _NestingAwareTransaction(project, "inner"):
                pass

        assert calls == ["outer", "inner"]
        assert project.Transaction.call_count == 2

    def test_phase1_never_touches_action_handler(self):
        """Phase 1 must not read CurrentDepth or construct a helper at all
        -- uses a strict double (no Mock auto-vivification) with no
        `project` (LcmCache) attribute at all, so any stray access would
        raise AttributeError instead of silently succeeding."""
        from flexicon.code.transaction import _NestingAwareTransaction

        class _StrictPhase1Project:
            def __init__(self):
                self.writeEnabled = True
                self._undoable = False
                self.transaction_calls = []

            def Transaction(self, label="transaction"):
                import contextlib

                self.transaction_calls.append(label)
                return contextlib.nullcontext()

        strict_project = _StrictPhase1Project()
        assert not hasattr(strict_project, "project")

        with _NestingAwareTransaction(strict_project, "label"):
            pass

        assert strict_project.transaction_calls == ["label"]


# ---------------------------------------------------------------------------
# 6. B3: Undo()/Redo() call through ActionHandlerAccessor, gated on
#    CanUndo()/CanRedo(), return False (not raise) when nothing to undo/redo.
# ---------------------------------------------------------------------------

class TestB3UndoRedo:
    def _make_project(self, undoable=True, can_undo=False, can_redo=False):
        ah = FaithfulActionHandler()
        ah._can_undo = can_undo
        ah._can_redo = can_redo
        project = Mock()
        project._undoable = undoable
        project.project = Mock()
        project.project.ActionHandlerAccessor = ah
        return project, ah

    def _get_flexproject_class(self):
        from flexicon.code.FLExProject import FLExProject

        return FLExProject

    def test_undo_returns_false_when_cannot_undo(self):
        FLExProject = self._get_flexproject_class()
        project, ah = self._make_project(can_undo=False)
        # Bind Undo/Redo from the real class onto our lightweight double so
        # we exercise the ACTUAL method body, not a re-implementation.
        result = FLExProject.Undo(project)
        assert result is False
        assert ah.undo_calls == 0

    def test_redo_returns_false_when_cannot_redo(self):
        FLExProject = self._get_flexproject_class()
        project, ah = self._make_project(can_redo=False)
        result = FLExProject.Redo(project)
        assert result is False
        assert ah.redo_calls == 0

    def test_undo_calls_through_action_handler_when_can_undo(self):
        FLExProject = self._get_flexproject_class()
        project, ah = self._make_project(can_undo=True)
        result = FLExProject.Undo(project)
        assert result is True
        assert ah.undo_calls == 1

    def test_redo_calls_through_action_handler_when_can_redo(self):
        FLExProject = self._get_flexproject_class()
        project, ah = self._make_project(can_redo=True)
        result = FLExProject.Redo(project)
        assert result is True
        assert ah.redo_calls == 1

    def test_undo_uses_action_handler_accessor_not_undo_stack(self):
        """
        Regression lock: Undo()/Redo() must read
        `self.project.ActionHandlerAccessor` (project.project is the LcmCache
        double) -- the non-existent `self.project.UndoStack` attribute must
        never be touched. A strict double (no auto-vivification) makes a
        stray `.UndoStack` access raise AttributeError immediately if the
        old code path ever reappears.
        """
        from flexicon.code.FLExProject import FLExProject

        class _StrictLcmCache:
            def __init__(self, action_handler):
                self.ActionHandlerAccessor = action_handler
                # Deliberately no UndoStack attribute at all.

        class _StrictProject:
            def __init__(self, action_handler):
                self._undoable = True
                self.project = _StrictLcmCache(action_handler)

        ah = FaithfulActionHandler()
        ah._can_undo = True
        ah._can_redo = True
        strict_project = _StrictProject(ah)

        assert FLExProject.Undo(strict_project) is True
        assert FLExProject.Redo(strict_project) is True
        assert ah.undo_calls == 1
        assert ah.redo_calls == 1

    def test_undo_raises_transaction_error_if_not_undoable(self):
        from flexicon.code.FLExProject import FLExProject, FP_TransactionError

        project = Mock()
        project._undoable = False

        with pytest.raises(FP_TransactionError):
            FLExProject.Undo(project)

    def test_redo_raises_transaction_error_if_not_undoable(self):
        from flexicon.code.FLExProject import FLExProject, FP_TransactionError

        project = Mock()
        project._undoable = False

        with pytest.raises(FP_TransactionError):
            FLExProject.Redo(project)

    def test_undo_wraps_unexpected_action_handler_exception(self):
        from flexicon.code.FLExProject import FLExProject, FP_TransactionError

        project, ah = self._make_project(can_undo=True)

        def _boom():
            raise RuntimeError("liblcm exploded")

        ah.Undo = _boom

        with pytest.raises(FP_TransactionError):
            FLExProject.Undo(project)

    def test_redo_wraps_unexpected_action_handler_exception(self):
        from flexicon.code.FLExProject import FLExProject, FP_TransactionError

        project, ah = self._make_project(can_redo=True)

        def _boom():
            raise RuntimeError("liblcm exploded")

        ah.Redo = _boom

        with pytest.raises(FP_TransactionError):
            FLExProject.Redo(project)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
