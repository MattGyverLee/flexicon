#
#   test_issue752_dependent_clause_hvo_live.py
#
#   Live gate for issue #752 DependentClausesRS HVO membership on AddDependentClause.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_752_"


@pytest.mark.requires_live_project
class TestIssue752DependentClauseHvoLive:
    """AddDependentClause must not rely on Python proxy identity in DependentClausesRS."""

    @pytest.mark.live_phase("ConstChartClauseMarkerOperations", "add")
    def test_add_dependent_clause_idempotent_via_resolved_hvo(self, target_sandbox):
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
            text = texts.Create(f"{TEST_PREFIX}text")
            paragraphs.Create(text, f"{TEST_PREFIX}one sentence.")
            para_list = list(text.ContentsOA.ParagraphsOS)
            para = IStTxtPara(para_list[0])
            seg = segments.AppendSentence(para, f"{TEST_PREFIX}one sentence.")
            if seg is None:
                segs = list(para.SegmentsOS)
                assert segs, "No segment for word group"
                seg = segs[0]

            chart = charts.Create(f"{TEST_PREFIX}chart")
            row = rows.Create(chart)
            wg_main = word_groups.Create(row, seg, seg)
            wg_dep = word_groups.Create(row, seg, seg)
            main_marker = clause_markers.Create(row, wg_main)
            dep_marker = clause_markers.Create(row, wg_dep)

            clause_markers.AddDependentClause(main_marker, dep_marker)
            assert len(clause_markers.GetDependentClauses(main_marker)) == 1

            resolved = target_sandbox.Object(int(dep_marker.Hvo))
            clause_markers.AddDependentClause(main_marker, resolved)
            assert len(clause_markers.GetDependentClauses(main_marker)) == 1
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
