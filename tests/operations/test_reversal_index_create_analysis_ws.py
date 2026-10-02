#
#   test_reversal_index_create_analysis_ws.py
#
#   Issue #605: ReversalIndexOperations.Create must reject a writing
#   system that is not one of the project's analysis writing systems,
#   before any mutation. Offline tests use a mocked project; the live
#   counterpart is test_reversal_index_create_analysis_ws_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from unittest.mock import MagicMock

import pytest

from flexicon.code.FLExProject import FP_ParameterError
from flexicon.code.Reversal.ReversalIndexOperations import ReversalIndexOperations


def _ws(handle, tag):
    ws = MagicMock()
    ws.Handle = handle
    ws.tag = tag
    return ws


def _make_ops(existing_indexes=()):
    en = _ws(10, "en")
    project = MagicMock()
    project.writeEnabled = True
    project.WritingSystems.GetAnalysis.return_value = [en]
    project.WritingSystems.GetLanguageTag.side_effect = lambda ws: ws.tag
    project.WSHandle.side_effect = lambda tag: {"en": 10, "qaa-x-vern": 20}.get(tag)
    ops = ReversalIndexOperations(project)
    ops.GetAll = MagicMock(return_value=list(existing_indexes))
    return ops, project


class TestReversalIndexCreateAnalysisWS:
    def test_vernacular_handle_raises_before_mutation(self):
        ops, project = _make_ops()
        with pytest.raises(FP_ParameterError):
            ops.Create("Vern", 20)
        project.lp.LexDbOA.ReversalIndexesOC.Add.assert_not_called()

    def test_vernacular_tag_raises_before_mutation(self):
        ops, project = _make_ops()
        with pytest.raises(FP_ParameterError):
            ops.Create("Vern", "qaa-x-vern")
        project.lp.LexDbOA.ReversalIndexesOC.Add.assert_not_called()

    def test_unknown_ws_raises(self):
        ops, _ = _make_ops()
        with pytest.raises(FP_ParameterError):
            ops.Create("Nope", "zz")

    @pytest.mark.parametrize("ws", [10, "en"])
    def test_analysis_ws_passes_validation(self, ws):
        ops, _ = _make_ops()
        try:
            ops.Create("English", ws)
        except FP_ParameterError as e:
            pytest.fail(f"analysis WS rejected: {e}")
        except Exception:
            pass  # past validation; later LCM factory calls are not available offline
