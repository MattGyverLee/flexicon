#
#   test_issue832_dependent_clause_rows_live.py
#
#   Live gate for issue #832: DependentClausesRS holds IConstChartRow, so
#   Add/Insert/RemoveDependentClause must round-trip rows through the LCM.
#
#   Copyright 2026
#

import logging

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_832_"


def _rs_hvos(project, marker_hvo):
    """Re-fetch the marker from the LCM and read DependentClausesRS HVOs."""
    from SIL.LCModel import IConstChartClauseMarker

    fresh = IConstChartClauseMarker(project.Object(int(marker_hvo)))
    return [int(r.Hvo) for r in fresh.DependentClausesRS], fresh


@pytest.mark.requires_live_project
class TestIssue832DependentClauseRowsLive:
    @pytest.mark.live_phase("ConstChartClauseMarkerOperations", "add")
    def test_dependent_clause_rows_round_trip(self, target_sandbox, caplog):
        from SIL.LCModel import ClauseTypes, IConstChartRow, IStTxtPara

        from flexicon.code.FLExProject import FP_ParameterError
        import flexicon.code.Discourse.ConstChartClauseMarkerOperations as mod

        project = target_sandbox
        charts = project.ConstCharts
        rows = project.ConstChartRows
        word_groups = project.ConstChartWordGroups
        clause_markers = project.ConstChartClauseMarkers
        texts = project.Texts
        paragraphs = project.Paragraphs
        segments = project.Segments

        chart = None
        text = None
        try:
            # 1. Build TEST_ data: text, chart, rows, clause marker.
            text = texts.Create(f"{TEST_PREFIX}text")
            paragraphs.Create(text, f"{TEST_PREFIX}one sentence.")
            para = IStTxtPara(list(text.ContentsOA.ParagraphsOS)[0])
            seg = segments.AppendSentence(para, f"{TEST_PREFIX}one sentence.")
            if seg is None:
                segs = list(para.SegmentsOS)
                assert segs, "No segment for word group"
                seg = segs[0]

            chart = charts.Create(f"{TEST_PREFIX}chart")
            host_row = rows.Create(chart)
            r1 = rows.Create(chart)
            r2 = rows.Create(chart)
            r3 = rows.Create(chart)
            r4_normal = rows.Create(chart)
            wg = word_groups.Create(host_row, seg, seg)
            marker = clause_markers.Create(host_row, wg)
            marker_hvo = int(marker.Hvo)

            # 2. Set ClauseType=Dependent on r1..r3 inside the ops object's own
            # transaction (no row Operations setter exists).
            with clause_markers._TransactionCM("TEST_832 set ClauseType"):
                for r in (r1, r2, r3):
                    IConstChartRow(r).ClauseType = ClauseTypes.Dependent
            assert IConstChartRow(project.Object(int(r4_normal.Hvo))).ClauseType == ClauseTypes.Normal
            for r in (r1, r2, r3):
                assert IConstChartRow(project.Object(int(r.Hvo))).ClauseType == ClauseTypes.Dependent

            print(
                "[EVIDENCE] marker_hvo=%d host_row=%d r1=%d r2=%d r3=%d r4_normal=%d"
                % (marker_hvo, int(host_row.Hvo), int(r1.Hvo), int(r2.Hvo),
                   int(r3.Hvo), int(r4_normal.Hvo))
            )
            before, _ = _rs_hvos(project, marker_hvo)
            assert before == []
            print("[EVIDENCE] pre-state RS=%s" % before)

            # 3. Add one row by object, another by HVO. Dependent rows: no warning.
            with caplog.at_level(logging.WARNING, logger=mod.__name__):
                clause_markers.AddDependentClause(marker, r1)
                clause_markers.AddDependentClause(marker_hvo, int(r2.Hvo))
            assert not [x for x in caplog.records if "[WARN]" in x.getMessage()]

            # 4. Re-fetch and assert.
            got, fresh = _rs_hvos(project, marker_hvo)
            assert got == [int(r1.Hvo), int(r2.Hvo)]
            assert all(r.ClassName == "ConstChartRow" for r in fresh.DependentClausesRS)
            print("[EVIDENCE] after add r1(obj), r2(hvo): RS=%s" % got)

            # 5. Re-add is unchanged; Insert at 0; Remove index 0.
            clause_markers.AddDependentClause(marker, r1)
            got, _ = _rs_hvos(project, marker_hvo)
            assert got == [int(r1.Hvo), int(r2.Hvo)]
            print("[EVIDENCE] after re-add r1: RS=%s" % got)

            clause_markers.InsertDependentClause(marker, 0, r3)
            got, fresh = _rs_hvos(project, marker_hvo)
            assert got == [int(r3.Hvo), int(r1.Hvo), int(r2.Hvo)]
            assert all(r.ClassName == "ConstChartRow" for r in fresh.DependentClausesRS)
            print("[EVIDENCE] after insert r3@0: RS=%s" % got)

            clause_markers.RemoveDependentClause(marker, 0)
            got, _ = _rs_hvos(project, marker_hvo)
            assert got == [int(r1.Hvo), int(r2.Hvo)]
            print("[EVIDENCE] after remove idx 0: RS=%s" % got)

            # 6. A Normal row produces the warning (and is still added).
            caplog.clear()
            with caplog.at_level(logging.WARNING, logger=mod.__name__):
                clause_markers.AddDependentClause(marker, r4_normal)
            warns = [x for x in caplog.records if "[WARN]" in x.getMessage()]
            assert warns, "expected [WARN] for a Normal row"
            got, _ = _rs_hvos(project, marker_hvo)
            assert got == [int(r1.Hvo), int(r2.Hvo), int(r4_normal.Hvo)]
            print("[EVIDENCE] after add Normal r4: RS=%s warnings=%d" % (got, len(warns)))

            deps = list(clause_markers.GetDependentClauses(marker_hvo))
            assert [int(d.Hvo) for d in deps] == got
            assert all(d.ClassName == "ConstChartRow" for d in deps)

            # 7. Passing a clause marker is rejected, RS unchanged.
            with pytest.raises(FP_ParameterError, match="IConstChartRow"):
                clause_markers.AddDependentClause(marker, marker)
            with pytest.raises(FP_ParameterError, match="IConstChartRow"):
                clause_markers.InsertDependentClause(marker, 0, marker_hvo)
            after, _ = _rs_hvos(project, marker_hvo)
            assert after == got
            print("[EVIDENCE] marker passed as element rejected; RS=%s" % after)
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
