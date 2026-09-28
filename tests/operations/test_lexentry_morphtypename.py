"""
Test Suite for LexEntryOperations.GetMorphTypeName()

Coverage for issue #583: there was no public wrapper taking an
already-resolved IMoMorphType (as returned by
LexEntryOperations.GetMorphType / AllomorphOperations.GetMorphType) and
returning its display name -- recipe ports fell through to raw
``ITsString(mt.Name.BestAnalysisAlternative).Text`` access.

Uses mocks for the FLExProject/LCM layer -- no live FieldWorks project
required.
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations


class _FakeMorphType:
    """Minimal IMoMorphType stand-in: a Name multistring mock."""

    def __init__(self, best_analysis_text=None, name_obj="default"):
        if name_obj == "default":
            self.Name = Mock(
                BestAnalysisAlternative=Mock(Text=best_analysis_text),
                get_String=Mock(),
            )
        else:
            # Lets callers pass name_obj=None for an unset Name.
            self.Name = name_obj


def _make_project():
    """Minimal mock FLExProject sufficient for the wsHandle path."""
    project = Mock()
    project.project.DefaultAnalWs = 1

    def _resolve_ws(ws, default):
        return default if ws is None else ws

    project._FLExProject__WSHandle = Mock(side_effect=_resolve_ws)
    return project


@pytest.fixture
def ops():
    return LexEntryOperations(_make_project())


class TestGetMorphTypeName:
    """Issue #583: name for an already-resolved morph type object."""

    def test_none_returns_empty_string(self, ops):
        assert ops.GetMorphTypeName(None) == ""

    def test_default_uses_best_analysis_alternative(self, ops):
        mt = _FakeMorphType(best_analysis_text="stem")
        assert ops.GetMorphTypeName(mt) == "stem"

    def test_default_never_touches_get_string(self, ops):
        mt = _FakeMorphType(best_analysis_text="suffix")
        assert ops.GetMorphTypeName(mt) == "suffix"
        mt.Name.get_String.assert_not_called()

    def test_null_marker_becomes_empty_string(self, ops):
        mt = _FakeMorphType(best_analysis_text="***")
        assert ops.GetMorphTypeName(mt) == ""

    def test_unset_name_returns_empty_string(self, ops):
        mt = _FakeMorphType(name_obj=None)
        assert ops.GetMorphTypeName(mt) == ""

    def test_explicit_ws_reads_that_writing_system(self, ops):
        mt = _FakeMorphType(best_analysis_text="stem")
        with patch(
            "flexicon.code.Lexicon.LexEntryOperations.ITsString"
        ) as mock_its:
            mock_its.return_value = Mock(Text="suffix")
            assert ops.GetMorphTypeName(mt, wsHandle=99) == "suffix"
        # The resolved writing system is what get_String saw.
        mt.Name.get_String.assert_called_once_with(99)

    def test_explicit_ws_null_marker_becomes_empty_string(self, ops):
        mt = _FakeMorphType(best_analysis_text="stem")
        with patch(
            "flexicon.code.Lexicon.LexEntryOperations.ITsString"
        ) as mock_its:
            mock_its.return_value = Mock(Text="***")
            assert ops.GetMorphTypeName(mt, wsHandle=99) == ""

    def test_works_for_allomorph_sourced_morph_type(self, ops):
        # IMoMorphType objects are shared between LexEntryOperations and
        # AllomorphOperations -- the same wrapper serves both.
        mt = _FakeMorphType(best_analysis_text="enclitic")
        assert ops.GetMorphTypeName(mt) == "enclitic"
