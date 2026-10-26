#
#   test_issue792_discourse_delete_hvo_live.py
#
#   Live verification for issue #792 DiscourseOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_792_"


class TestIssue792DiscourseDeleteHvoWriteGate:
    """DeleteChart/DeleteRow must remove members when passed bare Object(hvo) views."""

    @pytest.mark.live_phase("DiscourseOperations", "write")
    def test_delete_chart_removes_from_chartsoc_by_hvo(self, target_sandbox):
        project = target_sandbox
        texts = list(project.Texts.GetAll())
        if not texts:
            text = project.Texts.Create(f"{TEST_PREFIX}text")
        else:
            text = texts[0]
        chart = project.Discourse.CreateChart(text, f"{TEST_PREFIX}chart")
        owner = project.Discourse._GetTypedOwner(chart)
        assert owner is not None
        starting = owner.ChartsOC.Count
        hvo = chart.Hvo
        bare_view = project.Object(hvo)
        project.Discourse.DeleteChart(bare_view)
        assert owner.ChartsOC.Count == starting - 1
        assert not any(int(c.Hvo) == int(hvo) for c in owner.ChartsOC)

    @pytest.mark.live_phase("DiscourseOperations", "write")
    def test_delete_row_removes_from_rowsos_by_hvo(self, target_sandbox):
        project = target_sandbox
        texts = list(project.Texts.GetAll())
        if not texts:
            text = project.Texts.Create(f"{TEST_PREFIX}text_row")
        else:
            text = texts[0]
        chart = project.Discourse.CreateChart(text, f"{TEST_PREFIX}row_parent")
        row = project.Discourse.AddRow(chart)
        owner = project.Discourse._GetTypedOwner(row)
        assert owner is not None
        starting = owner.RowsOS.Count
        hvo = row.Hvo
        bare_view = project.Object(hvo)
        project.Discourse.DeleteRow(bare_view)
        assert owner.RowsOS.Count == starting - 1
        assert not any(int(r.Hvo) == int(hvo) for r in owner.RowsOS)
        try:
            project.Discourse.DeleteChart(chart.Hvo)
        except Exception:
            pass
