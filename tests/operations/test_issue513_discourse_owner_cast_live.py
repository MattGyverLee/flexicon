#
#   test_issue513_discourse_owner_cast_live.py
#
#   Live gate for issue #513: DiscourseOperations delete/duplicate must
#   reach ChartsOC/RowsOS when callers pass chart/row HVOs.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_513_"


class TestIssue513DiscourseOwnerCastWriteGate:
    """Delete and duplicate must work via HVO, not only typed chart objects."""

    @pytest.mark.live_phase("DiscourseOperations", "write")
    def test_delete_chart_via_hvo_removes_from_text(self, target_sandbox):
        texts = list(target_sandbox.Texts.GetAll())
        if not texts:
            pytest.skip("Target has no texts for chart delete gate")
        text = texts[0]
        name = f"{TEST_PREFIX}chart"
        chart = target_sandbox.Discourse.CreateChart(text, name)
        hvo = chart.Hvo
        before = len(list(target_sandbox.Discourse.GetAllCharts(text)))
        target_sandbox.Discourse.DeleteChart(hvo)
        after = len(list(target_sandbox.Discourse.GetAllCharts(text)))
        assert after == before - 1

    @pytest.mark.live_phase("DiscourseOperations", "write")
    def test_delete_row_via_hvo_updates_row_count(self, target_sandbox):
        texts = list(target_sandbox.Texts.GetAll())
        if not texts:
            pytest.skip("Target has no texts for row delete gate")
        text = texts[0]
        chart = target_sandbox.Discourse.CreateChart(text, f"{TEST_PREFIX}row_parent")
        row = target_sandbox.Discourse.AddRow(chart)
        row_hvo = row.Hvo
        assert target_sandbox.Discourse.GetRowCount(chart) >= 1
        target_sandbox.Discourse.DeleteRow(row_hvo)
        assert target_sandbox.Discourse.GetRowCount(chart.Hvo) == 0

    @pytest.mark.live_phase("DiscourseOperations", "write")
    def test_duplicate_via_hvo_attaches_to_parent(self, target_sandbox):
        texts = list(target_sandbox.Texts.GetAll())
        if not texts:
            pytest.skip("Target has no texts for duplicate gate")
        text = texts[0]
        chart = target_sandbox.Discourse.CreateChart(text, f"{TEST_PREFIX}dup_src")
        before = len(list(target_sandbox.Discourse.GetAllCharts(text)))
        dup = target_sandbox.Discourse.Duplicate(chart.Hvo, deep=False)
        after = len(list(target_sandbox.Discourse.GetAllCharts(text)))
        assert after == before + 1
        assert dup is not None
        assert dup.Hvo != chart.Hvo
        try:
            target_sandbox.Discourse.DeleteChart(dup.Hvo)
            target_sandbox.Discourse.DeleteChart(chart.Hvo)
        except Exception:
            pass
