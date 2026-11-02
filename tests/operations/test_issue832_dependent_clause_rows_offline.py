#
#   test_issue832_dependent_clause_rows_offline.py
#
#   Offline coverage for issue #832: DependentClausesRS holds IConstChartRow,
#   so Add/InsertDependentClause take a row (object or HVO), not a marker.
#
#   Copyright 2026
#

import logging
from unittest.mock import MagicMock

import pytest

import flexicon.code.Discourse.ConstChartClauseMarkerOperations as mod
from flexicon.code.Discourse.ConstChartClauseMarkerOperations import (
    ConstChartClauseMarkerOperations,
)
from flexicon.code.FLExProject import FP_ParameterError

_counter = [5000]


class _FakeRS:
    def __init__(self, items=None):
        self._items = list(items or [])

    @property
    def Count(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def Add(self, v):
        self._items.append(v)

    def Insert(self, i, v):
        self._items.insert(i, v)

    def RemoveAt(self, i):
        del self._items[i]


class _Row:
    ClassName = "ConstChartRow"

    def __init__(self, clause_type="Dependent"):
        _counter[0] += 1
        self.Hvo = _counter[0]
        self.ClauseType = clause_type


class _Marker:
    ClassName = "ConstChartClauseMarker"

    def __init__(self, deps=None):
        _counter[0] += 1
        self.Hvo = _counter[0]
        self.DependentClausesRS = _FakeRS(deps)


@pytest.fixture
def ops():
    project = MagicMock()
    project.writeEnabled = True
    project._undoable = False
    return ConstChartClauseMarkerOperations(project)


def _hvos(marker):
    return [r.Hvo for r in marker.DependentClausesRS]


class TestIssue832DependentClauseRows:
    def test_add_accepts_row_object(self, ops):
        marker, row = _Marker(), _Row()
        ops.AddDependentClause(marker, row)
        assert _hvos(marker) == [row.Hvo]

    def test_add_accepts_row_hvo(self, ops):
        marker, row = _Marker(), _Row()
        ops.project.Object.return_value = row
        ops.AddDependentClause(marker, row.Hvo)
        assert _hvos(marker) == [row.Hvo]

    def test_insert_accepts_row_object_and_hvo(self, ops):
        first, second = _Row(), _Row()
        marker = _Marker([first])
        ops.InsertDependentClause(marker, 0, second)
        assert _hvos(marker) == [second.Hvo, first.Hvo]
        third = _Row()
        ops.project.Object.return_value = third
        ops.InsertDependentClause(marker, 2, third.Hvo)
        assert _hvos(marker) == [second.Hvo, first.Hvo, third.Hvo]

    def test_add_marker_raises_parameter_error(self, ops):
        with pytest.raises(FP_ParameterError, match="IConstChartRow"):
            ops.AddDependentClause(_Marker(), _Marker())

    def test_insert_marker_raises_parameter_error(self, ops):
        with pytest.raises(FP_ParameterError, match="IConstChartRow"):
            ops.InsertDependentClause(_Marker(), 0, _Marker())

    def test_add_other_object_raises_parameter_error(self, ops):
        with pytest.raises(FP_ParameterError, match="IConstChartRow"):
            ops.AddDependentClause(_Marker(), object())

    def test_add_hvo_of_wrong_class_raises(self, ops):
        ops.project.Object.return_value = _Marker()
        with pytest.raises(FP_ParameterError, match="IConstChartRow"):
            ops.AddDependentClause(_Marker(), 123)

    def test_add_twice_is_idempotent(self, ops):
        marker, row = _Marker(), _Row()
        ops.AddDependentClause(marker, row)
        ops.AddDependentClause(marker, row)
        assert _hvos(marker) == [row.Hvo]

    def test_normal_row_logs_warning_but_adds(self, ops, caplog):
        marker, row = _Marker(), _Row("Normal")
        with caplog.at_level(logging.WARNING, logger=mod.__name__):
            ops.AddDependentClause(marker, row)
        assert _hvos(marker) == [row.Hvo]
        assert any(
            "[WARN]" in r.getMessage() and "StartDependentClauseGroup" in r.getMessage()
            for r in caplog.records
        )

    def test_insert_normal_row_logs_warning(self, ops, caplog):
        marker, row = _Marker(), _Row("Normal")
        with caplog.at_level(logging.WARNING, logger=mod.__name__):
            ops.InsertDependentClause(marker, 0, row)
        assert _hvos(marker) == [row.Hvo]
        assert any("[WARN]" in r.getMessage() for r in caplog.records)

    def test_dependent_row_logs_no_warning(self, ops, caplog):
        marker, row = _Marker(), _Row("Dependent")
        with caplog.at_level(logging.WARNING, logger=mod.__name__):
            ops.AddDependentClause(marker, row)
        assert not caplog.records

    def test_get_returns_rows(self, ops):
        rows = [_Row(), _Row()]
        marker = _Marker(rows)
        got = list(ops.GetDependentClauses(marker))
        assert [r.Hvo for r in got] == [r.Hvo for r in rows]
        assert all(r.ClassName == "ConstChartRow" for r in got)
