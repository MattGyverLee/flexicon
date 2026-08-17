#
#   test_undo_redo.py
#
#   Class: TestUndo, TestRedo, TestUndoRedoDocumentation
#          Mock-based unit tests for FLExProject.Undo()/Redo() (B3,
#          write-path-transactions). No live FLEx project or pythonnet
#          write required -- ``self.project`` (the LcmCache stand-in) is a
#          bare object exposing a fake ``ActionHandlerAccessor``.
#
#   Covers issue #235: Undo()/Redo() used to read the non-existent
#   `LcmCache.UndoStack`; they now read `LcmCache.ActionHandlerAccessor`,
#   gated on CanUndo()/CanRedo().
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _import_flexproject():
    try:
        from flexicon.code.FLExProject import FLExProject, FP_TransactionError
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"FLExProject not available: {exc}")
    return FLExProject, FP_TransactionError


def _bare_project(FLExProject, undoable=True):
    """A FLExProject instance that skips OpenProject()'s pythonnet calls."""
    project = FLExProject.__new__(FLExProject)
    project._undoable = undoable
    return project


class _FakeActionHandler:
    """
    Minimal ``IActionHandler`` double. Exposes only what Undo()/Redo() touch:
    ``CanUndo``/``CanRedo``/``Undo``/``Redo``. Deliberately has no
    ``UndoStack`` attribute at all -- the old, broken accessor (#235).
    """

    def __init__(self, can_undo=False, can_redo=False, raise_on=None):
        self._can_undo = can_undo
        self._can_redo = can_redo
        self._raise_on = raise_on  # "Undo" or "Redo", or None
        self.undo_calls = 0
        self.redo_calls = 0

    def CanUndo(self):
        return self._can_undo

    def CanRedo(self):
        return self._can_redo

    def Undo(self):
        self.undo_calls += 1
        if self._raise_on == "Undo":
            raise RuntimeError("simulated LCM failure")

    def Redo(self):
        self.redo_calls += 1
        if self._raise_on == "Redo":
            raise RuntimeError("simulated LCM failure")


class _FakeCache:
    """Stand-in for the LcmCache at ``FLExProject.project``."""

    def __init__(self, action_handler):
        self.ActionHandlerAccessor = action_handler


# ---------------------------------------------------------------------------
# Undo()
# ---------------------------------------------------------------------------


class TestUndo:
    def test_raises_if_not_undoable(self):
        FLExProject, FP_TransactionError = _import_flexproject()
        project = _bare_project(FLExProject, undoable=False)

        with pytest.raises(FP_TransactionError):
            project.Undo()

    def test_returns_false_and_does_not_call_undo_when_cannot_undo(self):
        FLExProject, _ = _import_flexproject()
        project = _bare_project(FLExProject, undoable=True)
        action_handler = _FakeActionHandler(can_undo=False)
        project.project = _FakeCache(action_handler)

        result = project.Undo()

        assert result is False
        assert action_handler.undo_calls == 0

    def test_returns_true_and_calls_undo_when_can_undo(self):
        FLExProject, _ = _import_flexproject()
        project = _bare_project(FLExProject, undoable=True)
        action_handler = _FakeActionHandler(can_undo=True)
        project.project = _FakeCache(action_handler)

        result = project.Undo()

        assert result is True
        assert action_handler.undo_calls == 1

    def test_wraps_unexpected_exception_as_fp_transaction_error(self):
        FLExProject, FP_TransactionError = _import_flexproject()
        project = _bare_project(FLExProject, undoable=True)
        action_handler = _FakeActionHandler(can_undo=True, raise_on="Undo")
        project.project = _FakeCache(action_handler)

        with pytest.raises(FP_TransactionError):
            project.Undo()

    def test_reads_action_handler_accessor_not_undo_stack(self):
        """
        Regression lock for #235: the source must read
        `self.project.ActionHandlerAccessor`, never the non-existent
        `self.project.UndoStack`.
        """
        source = (REPO_ROOT / "flexicon" / "code" / "FLExProject.py").read_text(encoding="utf-8")
        undo_idx = source.index("    def Undo(self):")
        redo_idx = source.index("    def Redo(self):")
        body = source[undo_idx:redo_idx]

        assert "self.project.ActionHandlerAccessor" in body
        assert "UndoStack" not in body

    def test_no_dead_undo_stack_is_none_branch(self):
        """
        The old `if undo_stack is None:` / `else:` discovery branches are
        gone -- Undo() calls CanUndo()/Undo() directly.
        """
        source = (REPO_ROOT / "flexicon" / "code" / "FLExProject.py").read_text(encoding="utf-8")
        undo_idx = source.index("    def Undo(self):")
        redo_idx = source.index("    def Redo(self):")
        body = source[undo_idx:redo_idx]

        assert "undo_stack is None" not in body
        assert "getattr(undo_stack" not in body


# ---------------------------------------------------------------------------
# Redo()
# ---------------------------------------------------------------------------


class TestRedo:
    def test_raises_if_not_undoable(self):
        FLExProject, FP_TransactionError = _import_flexproject()
        project = _bare_project(FLExProject, undoable=False)

        with pytest.raises(FP_TransactionError):
            project.Redo()

    def test_returns_false_and_does_not_call_redo_when_cannot_redo(self):
        FLExProject, _ = _import_flexproject()
        project = _bare_project(FLExProject, undoable=True)
        action_handler = _FakeActionHandler(can_redo=False)
        project.project = _FakeCache(action_handler)

        result = project.Redo()

        assert result is False
        assert action_handler.redo_calls == 0

    def test_returns_true_and_calls_redo_when_can_redo(self):
        FLExProject, _ = _import_flexproject()
        project = _bare_project(FLExProject, undoable=True)
        action_handler = _FakeActionHandler(can_redo=True)
        project.project = _FakeCache(action_handler)

        result = project.Redo()

        assert result is True
        assert action_handler.redo_calls == 1

    def test_wraps_unexpected_exception_as_fp_transaction_error(self):
        FLExProject, FP_TransactionError = _import_flexproject()
        project = _bare_project(FLExProject, undoable=True)
        action_handler = _FakeActionHandler(can_redo=True, raise_on="Redo")
        project.project = _FakeCache(action_handler)

        with pytest.raises(FP_TransactionError):
            project.Redo()

    def test_reads_action_handler_accessor_not_undo_stack(self):
        source = (REPO_ROOT / "flexicon" / "code" / "FLExProject.py").read_text(encoding="utf-8")
        redo_idx = source.index("    def Redo(self):")
        # Redo() is the last transaction-related method before the
        # "Advanced Operations" section marker.
        end_idx = source.index("# --- Advanced Operations ---")
        body = source[redo_idx:end_idx]

        assert "self.project.ActionHandlerAccessor" in body
        assert "UndoStack" not in body

    def test_no_dead_undo_stack_is_none_branch(self):
        source = (REPO_ROOT / "flexicon" / "code" / "FLExProject.py").read_text(encoding="utf-8")
        redo_idx = source.index("    def Redo(self):")
        end_idx = source.index("# --- Advanced Operations ---")
        body = source[redo_idx:end_idx]

        assert "undo_stack is None" not in body
        assert "getattr(undo_stack" not in body


# ---------------------------------------------------------------------------
# Docstring scope caveat (#235 closed as in-process-only)
# ---------------------------------------------------------------------------


class TestUndoRedoDocumentation:
    def test_undo_docstring_states_in_process_only_scope(self):
        FLExProject, _ = _import_flexproject()
        doc = FLExProject.Undo.__doc__
        assert doc is not None
        assert "in-process" in doc.lower()

    def test_redo_docstring_states_in_process_only_scope(self):
        FLExProject, _ = _import_flexproject()
        doc = FLExProject.Redo.__doc__
        assert doc is not None
        assert "in-process" in doc.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
