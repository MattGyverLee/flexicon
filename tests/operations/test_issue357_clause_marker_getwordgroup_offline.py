#
#   test_issue357_clause_marker_getwordgroup_offline.py
#
#   Offline coverage for GitHub issue #357:
#   ConstChartClauseMarkerOperations.GetWordGroup must not read WordGroupRA
#   (not on IConstChartClauseMarker); navigate via ColumnRA in CellsOS.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest


def _ops_module_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "flexicon"
        / "code"
        / "Discourse"
        / "ConstChartClauseMarkerOperations.py"
    )


def _load_const_chart_clause_marker_ops(monkeypatch):
    """Load operations module without importing flexicon package __init__."""
    flexicon = types.ModuleType("flexicon")
    flexicon_code = types.ModuleType("flexicon.code")
    flexicon_discourse = types.ModuleType("flexicon.code.Discourse")
    flexicon_flex = types.ModuleType("flexicon.code.FLExProject")
    flexicon_flex.FP_ParameterError = type("FP_ParameterError", (Exception,), {})
    flexicon_flex.FP_ReadOnlyError = type("FP_ReadOnlyError", (Exception,), {})
    flexicon_flex.FP_NullParameterError = type("FP_NullParameterError", (Exception,), {})

    base_ops = types.ModuleType("flexicon.code.BaseOperations")

    class _BaseOperations:
        def __init__(self, project):
            self.project = project

        def _EnsureWriteEnabled(self):
            if not getattr(self.project, "writeEnabled", False):
                raise flexicon_flex.FP_ReadOnlyError()

        def _ValidateParam(self, value, name):
            if value is None:
                raise flexicon_flex.FP_NullParameterError()

        def _GetTypedElements(self, gen):
            return list(gen)

        def _TransactionCM(self, _label):
            cm = MagicMock()
            cm.__enter__ = Mock(return_value=None)
            cm.__exit__ = Mock(return_value=False)
            return cm

    def _operations_method(fn):
        return fn

    def _wrap_enumerable(fn):
        return fn

    base_ops.BaseOperations = _BaseOperations
    base_ops.OperationsMethod = _operations_method
    base_ops.wrap_enumerable = _wrap_enumerable

    sil_lcm = types.ModuleType("SIL.LCModel")

    class _IConstChartWordGroup:
        pass

    class _IConstChartClauseMarker:
        pass

    sil_lcm.IConstChartClauseMarker = _IConstChartClauseMarker
    sil_lcm.IConstChartClauseMarkerFactory = type("Factory", (), {})
    sil_lcm.IConstChartRow = type("IConstChartRow", (), {})
    sil_lcm.IConstChartWordGroup = _IConstChartWordGroup

    sys.modules["flexicon"] = flexicon
    sys.modules["flexicon.code"] = flexicon_code
    sys.modules["flexicon.code.Discourse"] = flexicon_discourse
    sys.modules["flexicon.code.FLExProject"] = flexicon_flex
    sys.modules["flexicon.code.BaseOperations"] = base_ops
    sys.modules["SIL"] = types.ModuleType("SIL")
    sys.modules["SIL.LCModel"] = sil_lcm

    mod_name = "flexicon.code.Discourse.ConstChartClauseMarkerOperations"
    spec = importlib.util.spec_from_file_location(mod_name, _ops_module_path())
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "flexicon.code.Discourse"
    sys.modules[mod_name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod, _IConstChartWordGroup


class _FakeCellsOS(list):
    def Add(self, item):
        self.append(item)


class TestIssue357GetWordGroupSourceRatchet:
    def test_getwordgroup_does_not_reference_wordgroupra(self):
        source = _ops_module_path().read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "GetWordGroup":
                segment = ast.get_source_segment(source, node)
                assert segment is not None
                assert ".WordGroupRA" not in segment
                assert "hasattr(marker, \"WordGroupRA\")" not in segment
                assert "__WordGroupForClauseMarker" in segment
                return
        pytest.fail("GetWordGroup not found")

    def test_wordgroup_helper_navigates_columnra_in_cellsos(self):
        source = _ops_module_path().read_text(encoding="utf-8")
        helper = source.split("def __WordGroupForClauseMarker")[1].split(
            "def __ResolveObject"
        )[0]
        assert "__WordGroupForClauseMarker" in source
        assert "ColumnRA" in helper
        assert "ConstChartWordGroup" in helper
        assert ".WordGroupRA" not in helper


class TestIssue357GetWordGroupOffline:
    def test_getwordgroup_matches_columnra_in_owning_row(self, monkeypatch):
        mod, _FakeWG = _load_const_chart_clause_marker_ops(monkeypatch)
        ops = mod.ConstChartClauseMarkerOperations(Mock())

        column = Mock()
        column.Hvo = 42

        wg_match = Mock()
        wg_match.ClassName = "ConstChartWordGroup"
        wg_match.ColumnRA = column

        wg_other = Mock()
        wg_other.ClassName = "ConstChartWordGroup"
        wg_other.ColumnRA = Mock(Hvo=99)

        row = Mock()
        row.CellsOS = _FakeCellsOS([wg_other, wg_match])

        marker = Mock()
        marker.ClassName = "ConstChartClauseMarker"
        marker.ColumnRA = column
        marker.Owner = row
        marker.WordGroupRA = wg_other

        result = ops.GetWordGroup(marker)
        assert result is wg_match

    def test_getwordgroup_returns_none_without_columnra(self, monkeypatch):
        mod, _ = _load_const_chart_clause_marker_ops(monkeypatch)
        ops = mod.ConstChartClauseMarkerOperations(Mock())
        marker = Mock()
        marker.ClassName = "ConstChartClauseMarker"
        marker.ColumnRA = None
        marker.Owner = Mock(CellsOS=_FakeCellsOS())

        assert ops.GetWordGroup(marker) is None
