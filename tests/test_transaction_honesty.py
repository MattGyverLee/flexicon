#
#   test_transaction_honesty.py
#
#   Class: TestRefreshFromDisk, TestOneShotWarning, TestTransactionHonesty
#          Coverage for the write-path-transactions Track A "honesty pass"
#          (A2a-A2e) and A4 (RefreshFromDisk), specs/write-path-transactions.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import logging
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _import_flexproject():
    try:
        from flexicon.code.FLExProject import FLExProject, FP_ReadOnlyError
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"FLExProject not available: {exc}")
    return FLExProject, FP_ReadOnlyError


def _bare_project(FLExProject):
    """A FLExProject instance that skips OpenProject()'s pythonnet calls."""
    return FLExProject.__new__(FLExProject)


# ---------------------------------------------------------------------------
# A4 -- RefreshFromDisk()
# ---------------------------------------------------------------------------


class TestRefreshFromDisk:
    def test_raises_readonly_error_when_not_write_enabled(self):
        FLExProject, FP_ReadOnlyError = _import_flexproject()
        project = _bare_project(FLExProject)
        project.writeEnabled = False

        with pytest.raises(FP_ReadOnlyError):
            project.RefreshFromDisk()

    def test_calls_undo_stack_manager_refresh_when_write_enabled(self):
        from unittest.mock import MagicMock

        FLExProject, _ = _import_flexproject()
        project = _bare_project(FLExProject)
        project.writeEnabled = True

        mock_usm = MagicMock()
        project.ObjectRepository = MagicMock(return_value=mock_usm)

        project.RefreshFromDisk()

        mock_usm.Refresh.assert_called_once_with()

    def test_uses_same_accessor_pattern_as_save_changes(self):
        """
        RefreshFromDisk and SaveChanges must resolve IUndoStackManager via the
        same ObjectRepository(IUndoStackManager) accessor (source-level check,
        since both are one-line delegations).
        """
        source = (REPO_ROOT / "flexicon" / "code" / "FLExProject.py").read_text(encoding="utf-8")
        assert "def RefreshFromDisk(self):" in source
        # Both methods must resolve the same service.
        refresh_idx = source.index("def RefreshFromDisk(self):")
        save_idx = source.index("def SaveChanges(self):")
        refresh_body = source[refresh_idx : refresh_idx + 2500]
        save_body = source[save_idx : save_idx + 1000]
        assert "self.ObjectRepository(IUndoStackManager)" in refresh_body
        assert "self.ObjectRepository(IUndoStackManager)" in save_body
        assert "usm.Refresh()" in refresh_body


# ---------------------------------------------------------------------------
# A2d -- single one-shot warning at OpenProject time
# ---------------------------------------------------------------------------


class TestOneShotWarningAtOpenProject:
    def test_openproject_source_contains_single_warning_call_for_no_rollback_mode(self):
        """
        Static check: exactly one logger.warning(...) call inside the
        `writeEnabled and not undoable` branch of OpenProject, replacing the
        old per-Transaction() warning that used to fire from
        _GetTransactionAPI on every call.
        """
        source = (REPO_ROOT / "flexicon" / "code" / "FLExProject.py").read_text(encoding="utf-8")
        open_idx = source.index("def OpenProject(self, projectName")
        close_idx = source.index("def CloseProject(self):")
        open_project_body = source[open_idx:close_idx]

        assert "One-shot warning" in open_project_body or "one-shot warning" in open_project_body.lower()
        assert open_project_body.count("logging.getLogger(__name__).warning(") == 1

    def test_transaction_py_no_longer_logs_per_call_debug_for_missing_mark_api(self):
        """
        The per-Transaction() debug log that used to fire every time the
        (fictional) mark API was unavailable has been removed; the one-shot
        OpenProject() warning now carries that information instead.
        """
        source = (REPO_ROOT / "flexicon" / "code" / "transaction.py").read_text(encoding="utf-8")
        assert "LCM mark API unavailable" not in source


# ---------------------------------------------------------------------------
# A2a/A2b/A2c -- Transaction() honesty
# ---------------------------------------------------------------------------


class TestTransactionHonesty:
    def test_get_transaction_api_removed(self):
        FLExProject, _ = _import_flexproject()
        assert not hasattr(FLExProject, "_GetTransactionAPI")

    def test_transaction_keeps_its_name(self):
        """D4: Transaction() is NOT renamed to OperationGroup."""
        FLExProject, _ = _import_flexproject()
        assert hasattr(FLExProject, "Transaction")
        assert not hasattr(FLExProject, "OperationGroup")

    def test_transaction_docstring_states_no_rollback_under_undoable_false(self):
        FLExProject, _ = _import_flexproject()
        doc = FLExProject.Transaction.__doc__
        assert doc is not None
        assert "no rollback" in doc.lower() or "there is no rollback" in doc.lower()
        assert "session" in doc.lower()

    def test_transaction_docstring_no_longer_claims_per_mark_nesting_rollback(self):
        """
        The old Note block claimed nested Transaction() blocks each get an
        independent rollback mark. That behaviour never existed (the LCM
        API it depended on, RollbackToMark, does not exist) and must not
        survive in the docstring.
        """
        FLExProject, _ = _import_flexproject()
        doc = FLExProject.Transaction.__doc__
        assert "creating a separate mark token" not in doc
        assert "An inner rollback rolls back only to the inner" not in doc

    def test_transaction_body_always_passes_none_none(self):
        """
        Transaction() must construct _FLExTransaction with (None, None) --
        there is no discovery step left to run.
        """
        source = (REPO_ROOT / "flexicon" / "code" / "FLExProject.py").read_text(encoding="utf-8")
        txn_idx = source.index('def Transaction(self, label="transaction"):')
        save_idx = source.index("def SaveChanges(self):")
        body = source[txn_idx:save_idx]
        assert "_FLExTransaction(self, label, None, None)" in body

    def test_transaction_runs_body_and_reraises_without_rollback(self):
        """
        End-to-end (mock LCM) proof that Transaction() in the current build
        runs the body and re-raises on exception, with no rollback attempted
        (there is nothing to roll back to).
        """
        FLExProject, _ = _import_flexproject()
        project = _bare_project(FLExProject)
        project.writeEnabled = True

        ran = []
        with pytest.raises(RuntimeError, match="boom"):
            with project.Transaction("test"):
                ran.append(True)
                raise RuntimeError("boom")
        assert ran == [True]

    def test_baseoperations_transactioncm_docstring_no_longer_claims_rollback(self):
        """
        BaseOperations._TransactionCM's Notes section made the same false
        Phase 1 rollback claim as FLExProject.Transaction(); it must be
        corrected too (docstring-only change; behaviour/signature unchanged
        this cycle -- B1 rewrites the implementation next spurt).
        """
        try:
            from flexicon.code.BaseOperations import BaseOperations
        except Exception as exc:  # pragma: no cover - environment-dependent
            pytest.skip(f"BaseOperations not available: {exc}")

        doc = BaseOperations._TransactionCM.__doc__
        assert doc is not None
        assert "does NOT roll back" in doc or "does not roll back" in doc.lower()
        # The old false claim, verbatim, must be gone.
        assert "rolls back to a mark on exception." not in doc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
