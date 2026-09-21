#
#   test_352_discourse_live.py
#
#   Live regression coverage for issue #352 (Discourse face): chart-cell
#   types declare no Label/Comment, so Set/GetCellContent must not crash
#   on the multistring shape -- and must round-trip the bare-ITsString
#   Label that chart rows do carry.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


class Test352CellContentShapes:
    @pytest.mark.live_phase("DiscourseOperations", "add")
    def test_row_label_roundtrip(self, target_sandbox):
        charts = target_sandbox.ConstCharts
        rows = target_sandbox.ConstChartRows
        disc = target_sandbox.Discourse
        chart = charts.Create("TEST_352 chart")
        try:
            row = rows.Create(chart, label="TEST_352 row")
            try:
                assert disc.GetCellContent(row) == "TEST_352 row"
                disc.SetCellContent(row, "TEST_352 relabel")
                assert disc.GetCellContent(row) == "TEST_352 relabel"
                assert rows.GetLabel(row) == "TEST_352 relabel"
            finally:
                rows.Delete(row)
        finally:
            charts.Delete(chart)

    @pytest.mark.live_phase("DiscourseOperations", "read")
    def test_unsupported_cell_raises_actionable(self, target_sandbox):
        disc = target_sandbox.Discourse
        with pytest.raises(FP_ParameterError, match="editable content"):
            disc.SetCellContent(object(), "x")
