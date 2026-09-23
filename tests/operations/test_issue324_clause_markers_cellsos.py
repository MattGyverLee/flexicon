#
#   test_issue324_clause_markers_cellsos.py
#
#   Regression coverage for GitHub issue #324:
#   ConstChartClauseMarkerOperations used the nonexistent
#   IConstChartRow.ClauseMarkersOS; clause markers live in CellsOS.
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


class _FakeCellsOS(list):
    def Add(self, item):
        self.append(item)


class TestIssue324ClauseMarkersCellsOSOffline:
    """Mock-only: Create attaches to CellsOS; GetAll filters by ClassName."""

    def _ops(self):
        project = Mock()
        project.writeEnabled = True
        project.project = Mock()
        project.project.ServiceLocator = Mock()
        marker = Mock()
        marker.ClassName = "ConstChartClauseMarker"
        marker.Hvo = 9001
        factory = Mock()
        factory.Create.return_value = marker
        project.project.ServiceLocator.GetService.return_value = factory
        ops = ConstChartClauseMarkerOperations(project)
        ops._TransactionCM = MagicMock()
        ops._TransactionCM.return_value.__enter__ = Mock(return_value=None)
        ops._TransactionCM.return_value.__exit__ = Mock(return_value=False)
        return ops, marker

    def test_create_adds_to_cellsos_not_clausemarkersos(self, monkeypatch):
        import flexicon.code.Discourse.ConstChartClauseMarkerOperations as mod

        # Create() type-guards with isinstance(word_group, IConstChartWordGroup)
        # (#371); substitute a plain class so the double passes that guard.
        class _FakeWordGroup:
            ColumnRA = None

        monkeypatch.setattr(mod, "IConstChartWordGroup", _FakeWordGroup)

        ops, marker = self._ops()
        row = Mock()
        row.ClassName = "ConstChartRow"
        row.CellsOS = _FakeCellsOS()
        row.ClauseMarkersOS = Mock()
        wg = _FakeWordGroup()

        result = ops.Create(row, wg)

        assert result is marker
        assert marker in row.CellsOS
        row.ClauseMarkersOS.Add.assert_not_called()

    def test_getall_returns_only_clause_markers_from_cellsos(self):
        ops, _ = self._ops()
        row = Mock()
        row.ClassName = "ConstChartRow"
        wg_cell = Mock()
        wg_cell.ClassName = "ConstChartWordGroup"
        cm_cell = Mock()
        cm_cell.ClassName = "ConstChartClauseMarker"
        row.CellsOS = _FakeCellsOS([wg_cell, cm_cell])

        # _GetTypedElements casts; for mock, patch to identity on ClassName match
        ops._GetTypedElements = lambda gen: list(gen)

        got = ops.GetAll(row)
        assert got == [cm_cell]

    def test_find_by_index_uses_filtered_cellsos_order(self):
        ops, _ = self._ops()
        row = Mock()
        row.ClassName = "ConstChartRow"
        first = Mock()
        first.ClassName = "ConstChartClauseMarker"
        second = Mock()
        second.ClassName = "ConstChartClauseMarker"
        row.CellsOS = _FakeCellsOS([first, second])
        ops._GetTypedElements = lambda gen: list(gen)

        assert ops.Find(row, 0) is first
        assert ops.Find(row, 1) is second
        assert ops.Find(row, 2) is None


@pytest.mark.requires_live_project
class TestIssue324ClauseMarkersCellsOSLive:
    """Live: Create persists marker in row.CellsOS; GetAll sees it."""

    TEST_PREFIX = "TEST_324_"

    @pytest.mark.live_phase("ConstChartClauseMarkerOperations", "add")
    def test_create_persists_in_cellsos_and_getall(self, target_sandbox):
        from SIL.LCModel import IStTxtPara

        charts = target_sandbox.ConstCharts
        rows = target_sandbox.ConstChartRows
        word_groups = target_sandbox.ConstChartWordGroups
        clause_markers = target_sandbox.ConstChartClauseMarkers
        texts = target_sandbox.Texts
        paragraphs = target_sandbox.Paragraphs
        segments = target_sandbox.Segments

        chart = None
        text = None
        try:
            text = texts.Create(f"{self.TEST_PREFIX}text")
            paragraphs.Create(text, f"{self.TEST_PREFIX}one sentence.")
            para_list = list(text.ContentsOA.ParagraphsOS)
            para = IStTxtPara(para_list[0])
            seg = segments.AppendSentence(para, f"{self.TEST_PREFIX}one sentence.")
            if seg is None:
                segs = list(para.SegmentsOS)
                assert segs, "No segment for word group"
                seg = segs[0]

            chart = charts.Create(f"{self.TEST_PREFIX}chart")
            row = rows.Create(chart)
            assert row.CellsOS.Count == 0

            wg = word_groups.Create(row, seg, seg)
            marker = clause_markers.Create(row, wg)
            marker_hvo = marker.Hvo

            cells_hvos = [c.Hvo for c in row.CellsOS]
            assert marker_hvo in cells_hvos, (
                f"Marker HVO {marker_hvo} not in row.CellsOS: {cells_hvos}"
            )

            got = list(clause_markers.GetAll(row))
            assert len(got) == 1 and got[0].Hvo == marker_hvo
            assert clause_markers.Find(row, 0).Hvo == marker_hvo

            clause_markers.Delete(marker)
            assert marker_hvo not in [c.Hvo for c in row.CellsOS]
        finally:
            if chart is not None:
                try:
                    charts.Delete(chart)
                except Exception:
                    pass
            if text is not None:
                try:
                    texts.Delete(text)
                except Exception:
                    pass
