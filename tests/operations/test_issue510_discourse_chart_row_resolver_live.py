#
#   test_issue510_discourse_chart_row_resolver_live.py
#
#   Live gate for issue #510 DiscourseOperations chart/row resolver cast.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_510_"


class TestIssue510DiscourseChartRowResolverHvoGate:
    """Chart/row helpers must accept HVO ints and raw ICmObject views."""

    @pytest.mark.live_phase("DiscourseOperations", "read")
    def test_get_chart_name_accepts_chart_hvo_and_raw_object(self, sena3_sandbox):
        charts = list(sena3_sandbox.ConstCharts.GetAll())
        if not charts:
            pytest.skip("Sena 3 has no constituent charts for gate")
        chart = charts[0]
        name_via_obj = sena3_sandbox.Discourse.GetChartName(chart)
        name_via_hvo = sena3_sandbox.Discourse.GetChartName(chart.Hvo)
        raw = sena3_sandbox.Object(chart.Hvo)
        name_via_raw = sena3_sandbox.Discourse.GetChartName(raw)
        assert name_via_hvo == name_via_obj
        assert name_via_raw == name_via_obj

    @pytest.mark.live_phase("DiscourseOperations", "read")
    def test_get_rows_accepts_chart_hvo_and_raw_object(self, sena3_sandbox):
        charts = list(sena3_sandbox.ConstCharts.GetAll())
        if not charts:
            pytest.skip("Sena 3 has no constituent charts for gate")
        chart = charts[0]
        rows_obj = list(sena3_sandbox.Discourse.GetRows(chart))
        rows_hvo = list(sena3_sandbox.Discourse.GetRows(chart.Hvo))
        raw = sena3_sandbox.Object(chart.Hvo)
        rows_raw = list(sena3_sandbox.Discourse.GetRows(raw))
        assert len(rows_hvo) == len(rows_obj)
        assert len(rows_raw) == len(rows_obj)
