#
#   test_issue292_sync_foreign_changes_offline.py
#
#   Offline coverage for issue #292: SyncForeignChanges mid-session save.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pathlib
from unittest.mock import MagicMock

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
FLEX_PROJECT = REPO_ROOT / "flexicon" / "code" / "FLExProject.py"


def _import_flexproject():
    try:
        from flexicon.code.FLExProject import (
            FLExProject,
            FP_ReadOnlyError,
            FP_RuntimeError,
            FP_TransactionError,
        )
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"FLExProject not available: {exc}")
    return FLExProject, FP_ReadOnlyError, FP_RuntimeError, FP_TransactionError


def _bare_project(FLExProject, *, undoable=False, write_enabled=True):
    project = FLExProject.__new__(FLExProject)
    project.writeEnabled = write_enabled
    project._undoable = undoable
    project.project = MagicMock()
    project.project.MainCacheAccessor = MagicMock()
    return project


class TestIssue292SyncForeignChangesOffline:
    def test_method_exists_in_source(self):
        text = FLEX_PROJECT.read_text(encoding="utf-8")
        assert "def SyncForeignChanges(self):" in text
        assert "EndNonUndoableTask()" in text
        assert "BeginNonUndoableTask()" in text

    def test_ruling_document_exists(self):
        ruling = REPO_ROOT / "specs" / "292-sync-foreign-changes" / "rulings.md"
        assert ruling.is_file()

    def test_readonly_refused(self):
        FLExProject, FP_ReadOnlyError, _, _ = _import_flexproject()
        project = _bare_project(FLExProject, write_enabled=False)
        with pytest.raises(FP_ReadOnlyError):
            project.SyncForeignChanges()

    def test_attached_view_refused(self):
        FLExProject, _, FP_RuntimeError, _ = _import_flexproject()
        project = _bare_project(FLExProject)
        project._attached_donor = object()
        with pytest.raises(FP_RuntimeError, match="SyncForeignChanges"):
            project.SyncForeignChanges()

    def test_undoable_mode_refused(self):
        FLExProject, _, _, FP_TransactionError = _import_flexproject()
        project = _bare_project(FLExProject, undoable=True)
        project.project.ActionHandlerAccessor.CurrentDepth = 1  # CurrentDepth is a read-only property (#243)
        with pytest.raises(FP_TransactionError, match="undoable=False"):
            project.SyncForeignChanges()

    def test_depth_zero_refused(self):
        FLExProject, _, _, FP_TransactionError = _import_flexproject()
        project = _bare_project(FLExProject, undoable=False)
        project.project.ActionHandlerAccessor.CurrentDepth = 0  # CurrentDepth is a read-only property (#243)
        project.HasOpenSessionTask = MagicMock(return_value=False)
        with pytest.raises(FP_TransactionError, match="SaveChanges"):
            project.SyncForeignChanges()

    def test_end_save_begin_sequence_at_depth_one(self):
        FLExProject, _, _, _ = _import_flexproject()
        project = _bare_project(FLExProject, undoable=False)
        project.project.ActionHandlerAccessor.CurrentDepth = 1  # CurrentDepth is a read-only property (#243)
        project.HasOpenSessionTask = MagicMock(return_value=True)
        mock_usm = MagicMock()
        project.ObjectRepository = MagicMock(return_value=mock_usm)
        calls = []

        def _end():
            calls.append("end")

        def _begin():
            calls.append("begin")

        project.project.MainCacheAccessor.EndNonUndoableTask.side_effect = _end
        project.project.MainCacheAccessor.BeginNonUndoableTask.side_effect = _begin

        project.SyncForeignChanges()

        assert calls == ["end", "begin"]
        mock_usm.Save.assert_called_once_with()
        project.project.MainCacheAccessor.EndNonUndoableTask.assert_called_once()
        project.project.MainCacheAccessor.BeginNonUndoableTask.assert_called_once()

    def test_reopens_envelope_when_save_raises(self):
        FLExProject, _, _, _ = _import_flexproject()
        project = _bare_project(FLExProject, undoable=False)
        project.project.ActionHandlerAccessor.CurrentDepth = 1  # CurrentDepth is a read-only property (#243)
        project.HasOpenSessionTask = MagicMock(return_value=True)
        mock_usm = MagicMock()
        mock_usm.Save.side_effect = RuntimeError("save failed")
        project.ObjectRepository = MagicMock(return_value=mock_usm)

        with pytest.raises(RuntimeError, match="save failed"):
            project.SyncForeignChanges()

        project.project.MainCacheAccessor.BeginNonUndoableTask.assert_called_once()
