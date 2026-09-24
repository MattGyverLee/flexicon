#
#   test_issue230_dependent_clauses_rs.py
#
#   Offline coverage for issue #230: DependentClausesRS insert/remove write API
#   on ConstChartClauseMarkerOperations (sibling to SegmentOperations #215).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from unittest.mock import MagicMock, Mock

import pytest

from flexicon.code.Discourse.ConstChartClauseMarkerOperations import (
    ConstChartClauseMarkerOperations,
)
from flexicon.code.FLExProject import FP_ParameterError, FP_ReadOnlyError


class _FakeDependentClausesRS:
    """Minimal stand-in for IConstChartClauseMarker.DependentClausesRS."""

    def __init__(self, items=None):
        self._items = list(items) if items else []

    @property
    def Count(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __contains__(self, item):
        return item in self._items

    def Insert(self, index, value):
        self._items.insert(index, value)

    def Add(self, value):
        self._items.append(value)

    def RemoveAt(self, index):
        del self._items[index]


class TestIssue230DependentClausesRSWriteMethods:
    @pytest.fixture
    def writable_ops(self, monkeypatch):
        import flexicon.code.Discourse.ConstChartClauseMarkerOperations as mod

        class _FakeClauseMarker:
            pass

        monkeypatch.setattr(mod, "IConstChartClauseMarker", _FakeClauseMarker)

        mock_project = MagicMock()
        mock_project.writeEnabled = True
        mock_project._undoable = False
        ops = ConstChartClauseMarkerOperations(mock_project)
        return ops, _FakeClauseMarker

    @pytest.fixture
    def readonly_ops(self, monkeypatch):
        import flexicon.code.Discourse.ConstChartClauseMarkerOperations as mod

        class _FakeClauseMarker:
            pass

        monkeypatch.setattr(mod, "IConstChartClauseMarker", _FakeClauseMarker)

        mock_project = Mock()
        mock_project.writeEnabled = False
        ops = ConstChartClauseMarkerOperations(mock_project)
        return ops, _FakeClauseMarker

    def _make_marker(self, dependents=None):
        marker = Mock()
        marker.ClassName = "ConstChartClauseMarker"
        marker.DependentClausesRS = _FakeDependentClausesRS(dependents)
        return marker

    def test_InsertDependentClause_inserts_at_index(self, writable_ops):
        ops, cls = writable_ops
        dep_a, dep_b, new_dep = cls(), cls(), cls()
        marker = self._make_marker([dep_a, dep_b])

        ops.InsertDependentClause(marker, 1, new_dep)

        assert list(marker.DependentClausesRS) == [dep_a, new_dep, dep_b]

    def test_InsertDependentClause_allows_index_equal_to_count(self, writable_ops):
        ops, cls = writable_ops
        dep_a, new_dep = cls(), cls()
        marker = self._make_marker([dep_a])

        ops.InsertDependentClause(marker, 1, new_dep)

        assert list(marker.DependentClausesRS) == [dep_a, new_dep]

    def test_InsertDependentClause_raises_on_out_of_range_index(self, writable_ops):
        ops, cls = writable_ops
        marker = self._make_marker([cls()])

        with pytest.raises(FP_ParameterError, match="index must be between"):
            ops.InsertDependentClause(marker, 5, cls())

    def test_InsertDependentClause_raises_on_invalid_type(self, writable_ops):
        ops, _cls = writable_ops
        marker = self._make_marker([])

        with pytest.raises(FP_ParameterError, match="IConstChartClauseMarker"):
            ops.InsertDependentClause(marker, 0, object())

    def test_InsertDependentClause_raises_on_readonly(self, readonly_ops):
        ops, cls = readonly_ops
        marker = self._make_marker([])

        with pytest.raises(FP_ReadOnlyError):
            ops.InsertDependentClause(marker, 0, cls())

    def test_RemoveDependentClause_removes_at_index(self, writable_ops):
        ops, cls = writable_ops
        dep_a, dep_b, dep_c = cls(), cls(), cls()
        marker = self._make_marker([dep_a, dep_b, dep_c])

        ops.RemoveDependentClause(marker, 1)

        assert list(marker.DependentClausesRS) == [dep_a, dep_c]

    def test_RemoveDependentClause_raises_on_out_of_range_index(self, writable_ops):
        ops, cls = writable_ops
        marker = self._make_marker([cls()])

        with pytest.raises(FP_ParameterError, match="index must be between"):
            ops.RemoveDependentClause(marker, 3)

    def test_RemoveDependentClause_raises_on_readonly(self, readonly_ops):
        ops, cls = readonly_ops
        marker = self._make_marker([cls()])

        with pytest.raises(FP_ReadOnlyError):
            ops.RemoveDependentClause(marker, 0)
