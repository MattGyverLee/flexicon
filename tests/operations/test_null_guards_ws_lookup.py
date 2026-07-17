#
#   test_null_guards_ws_lookup.py
#
#   Class: TestReversalEntryWSNullGuard / TestProjectSettingsWSNullGuard
#          Regression coverage for the null-guards introduced in
#          fd156ee (closes #219).
#
#   fd156ee added two null-guards:
#     1. Reversal/ReversalIndexEntryOperations.__GetEntryWS now raises
#        FP_ParameterError (naming entry.Hvo) when entry.ReversalIndex
#        is None, instead of raising a NullReferenceException when
#        dereferencing index.WritingSystem on an orphaned/cascade-deleted
#        reversal entry.
#     2. System/ProjectSettingsOperations.GetAnalysisWritingSystem and
#        GetVernacularWritingSystem now return None when
#        project.lp is unavailable, instead of dereferencing
#        project.lp.DefaultAnalysisWritingSystem /
#        project.lp.DefaultVernacularWritingSystem on a None object.
#
#   These tests use MOCKED-CACHE fixtures (Mock project, no live
#   FieldWorks connection required), as explicitly accepted by issue
#   #219. Each guarded getter is exercised on BOTH the null-guard path
#   (guard triggers) and the normal populated path (guard passes
#   through unchanged), so the tests lock the pattern rather than
#   just the guard's existence.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from unittest.mock import Mock

import pytest

from flexicon.code.Reversal.ReversalIndexEntryOperations import (
    ReversalIndexEntryOperations,
)
from flexicon.code.System.ProjectSettingsOperations import (
    ProjectSettingsOperations,
)
from flexicon.code.FLExProject import FP_ParameterError


# =============================================================================
# Reversal WS lookup (ReversalIndexEntryOperations.__GetEntryWS)
# =============================================================================


class TestReversalEntryWSNullGuard:
    """Regression coverage for the reversal entry WS lookup null-guard."""

    def _make_ops(self):
        mock_project = Mock()
        mock_project.writeEnabled = True
        return ReversalIndexEntryOperations(mock_project), mock_project

    def _call_private_ws_lookup(self, ops, entry):
        # __GetEntryWS is name-mangled (double leading underscore); access
        # it directly to lock the guard itself without also depending on
        # ITsString/TsStringUtils plumbing in GetForm/SetForm.
        return ops._ReversalIndexEntryOperations__GetEntryWS(entry)

    def test_get_entry_ws_raises_when_reversal_index_none(self):
        """Guard triggers: orphaned/cascade-deleted entry with no owning index."""
        ops, _ = self._make_ops()
        entry = Mock()
        entry.ReversalIndex = None
        entry.Hvo = 4242

        with pytest.raises(FP_ParameterError) as excinfo:
            self._call_private_ws_lookup(ops, entry)

        assert "4242" in str(excinfo.value)

    def test_get_entry_ws_returns_handle_when_reversal_index_present(self):
        """Guard passes through: normal entry with a valid owning index."""
        ops, mock_project = self._make_ops()

        index = Mock()
        index.WritingSystem = "en"
        entry = Mock()
        entry.ReversalIndex = index
        entry.Hvo = 100

        mock_project.WSHandle.return_value = 7

        result = self._call_private_ws_lookup(ops, entry)

        assert result == 7
        mock_project.WSHandle.assert_called_once_with("en")

    def test_get_form_raises_on_orphaned_entry(self):
        """
        Integration path: GetForm(entry) with no explicit wsHandle falls
        through to __GetEntryWS. This is the exact NullReferenceException
        scenario fixed by fd156ee (reversal cleanup of orphaned entries).
        """
        ops, _ = self._make_ops()
        entry = Mock()
        entry.ReversalIndex = None
        entry.Hvo = 555

        with pytest.raises(FP_ParameterError) as excinfo:
            ops.GetForm(entry)

        assert "555" in str(excinfo.value)

    def test_set_form_raises_on_orphaned_entry(self):
        """SetForm(entry, text) with no explicit wsHandle also hits the guard."""
        ops, mock_project = self._make_ops()
        entry = Mock()
        entry.ReversalIndex = None
        entry.Hvo = 777

        with pytest.raises(FP_ParameterError) as excinfo:
            ops.SetForm(entry, "running")

        assert "777" in str(excinfo.value)


# =============================================================================
# ProjectSettings WS getters (GetAnalysisWritingSystem / GetVernacularWritingSystem)
# =============================================================================


class TestProjectSettingsWSNullGuard:
    """Regression coverage for the ProjectSettings WS getter null-guards."""

    def _make_ops(self, lp):
        mock_project = Mock()
        mock_project.lp = lp
        return ProjectSettingsOperations(mock_project)

    def test_get_analysis_writing_system_returns_none_when_lp_none(self):
        """Guard triggers: project.lp is None (language project unavailable)."""
        ops = self._make_ops(lp=None)
        assert ops.GetAnalysisWritingSystem() is None

    def test_get_analysis_writing_system_returns_default_ws_when_lp_present(self):
        """Guard passes through: project.lp is populated."""
        expected_ws = Mock()
        lp = Mock()
        lp.DefaultAnalysisWritingSystem = expected_ws
        ops = self._make_ops(lp=lp)

        assert ops.GetAnalysisWritingSystem() is expected_ws

    def test_get_vernacular_writing_system_returns_none_when_lp_none(self):
        """Guard triggers: project.lp is None (language project unavailable)."""
        ops = self._make_ops(lp=None)
        assert ops.GetVernacularWritingSystem() is None

    def test_get_vernacular_writing_system_returns_default_ws_when_lp_present(self):
        """Guard passes through: project.lp is populated."""
        expected_ws = Mock()
        lp = Mock()
        lp.DefaultVernacularWritingSystem = expected_ws
        ops = self._make_ops(lp=lp)

        assert ops.GetVernacularWritingSystem() is expected_ws
