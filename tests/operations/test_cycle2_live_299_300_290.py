#
#   test_cycle2_live_299_300_290.py
#
#   Consolidated live-LCM verification for the working-tree changes
#   covering issues #300, #299, and #290 (spec dir
#   299-300-290-reorder-and-tsstring). One session, three claims:
#
#     (A) #300 -- WfiMorphBundleOperations._GetSequence and
#         DataNotebookOperations._GetSequence now return the real
#         MorphBundlesOS / SubRecordsOS properties (the old
#         MorphsOS / RecordsOS names do not exist on the live parents).
#
#     (B) #299 -- ParagraphOperations._GetSequence now targets a text
#         paragraphsOS (not a paragraph segmentsOS), SegmentOperations
#         _GetSequence now targets a paragraph segmentsOS (not
#         AnalysesRS), and TextOperations._GetSequence is REMOVED so
#         project.Texts.Sort()/MoveUp() raise NotImplementedError live.
#
#     (C) #290 -- ConstChartRowOperations.Label/.Notes now route through
#         the house _MakeTsString/_ReadTsString idiom (bare ITsString,
#         not IMultiString).
#
#   Fixture: target_sandbox only (fresh tempdir copy of the Target
#   .fwbackup). Every test writes and re-queries from the live LCM.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import json
import pathlib

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_C2_"

_EVIDENCE_DIR = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "specs" / "299-300-290-reorder-and-tsstring" / "evidence"
)
_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
_EVIDENCE_JSON_PATH = _EVIDENCE_DIR / "live-cycle2-raw.json"


def _write_evidence(section, evidence):
    existing = {}
    if _EVIDENCE_JSON_PATH.exists():
        try:
            existing = json.loads(_EVIDENCE_JSON_PATH.read_text())
        except Exception:
            existing = {}
    existing[section] = evidence
    _EVIDENCE_JSON_PATH.write_text(json.dumps(existing, indent=2, default=str))


class TestIssue300WfiMorphBundleGetSequence:

    @pytest.mark.live_phase("WfiMorphBundleOperations", "reorder")
    def test_morph_bundle_reorder_hits_morphbundleos_not_morphsos(self, target_sandbox):
        wordforms = target_sandbox.Wordforms
        analyses = target_sandbox.WfiAnalyses
        bundles = target_sandbox.WfiMorphBundles
        evidence = {}

        wf = wordforms.Create(f"{TEST_PREFIX}hlaukalonga")
        analysis = analyses.Create(wf)

        evidence["parent_has_MorphsOS"] = hasattr(analysis, "MorphsOS")
        evidence["parent_has_MorphBundlesOS"] = hasattr(analysis, "MorphBundlesOS")
        assert not hasattr(analysis, "MorphsOS")
        assert hasattr(analysis, "MorphBundlesOS")

        b1 = bundles.Create(analysis)
        b2 = bundles.Create(analysis)
        b3 = bundles.Create(analysis)

        pre_order = [b.Hvo for b in analysis.MorphBundlesOS]
        evidence["pre_order_hvo"] = pre_order
        assert pre_order == [b1.Hvo, b2.Hvo, b3.Hvo]

        bundles.MoveDown(analysis, b1, 1)
        after_movedown = [b.Hvo for b in analysis.MorphBundlesOS]
        evidence["after_movedown_hvo"] = after_movedown
        assert after_movedown == [b2.Hvo, b1.Hvo, b3.Hvo]

        bundles.MoveUp(analysis, b3, 2)
        after_moveup = [b.Hvo for b in analysis.MorphBundlesOS]
        evidence["after_moveup_hvo"] = after_moveup
        assert after_moveup == [b3.Hvo, b2.Hvo, b1.Hvo]

        bundles.MoveToIndex(analysis, b2, 0)
        after_movetoindex = [b.Hvo for b in analysis.MorphBundlesOS]
        evidence["after_movetoindex_hvo"] = after_movetoindex
        assert after_movetoindex == [b2.Hvo, b3.Hvo, b1.Hvo]

        _write_evidence("300_wfimorphbundle", evidence)


class TestIssue300DataNotebookGetSequence:

    @pytest.mark.live_phase("DataNotebookOperations", "reorder")
    def test_subrecord_reorder_hits_subrecordsos_not_recordsos(self, target_sandbox):
        from SIL.LCModel import IRnGenericRecFactory

        notebook = target_sandbox.DataNotebook
        evidence = {}

        # ROUTE AROUND two separate, pre-existing live defects found
        # during this verification session (both out of #300's scope,
        # which only touched _GetSequence):
        #   1. DataNotebookOperations.Create() calls
        #      repos.RecordsOC.Add(record) on the IRnResearchNbkRepository
        #      service, but that repository has no RecordsOC member live
        #      (confirmed: AttributeError). The real owning collection is
        #      LangProject.ResearchNotebookOA.RecordsOC.
        #   2. DataNotebookOperations.__GetRecordObject (used by
        #      CreateSubRecord/SetTitle/etc.) calls
        #      self.project.project.GetObject(hvo), but LcmCache has no
        #      GetObject member live (confirmed: AttributeError) -- the
        #      house pattern is self.project.Object(hvo) (see
        #      BaseOperations._GetObject).
        # Both bugs block the whole DataNotebookOperations CRUD surface
        # for records/sub-records. Build the parent + 3 sub-records
        # directly against the real LCM factories/collections so this
        # test can reach SubRecordsOS and the reordering path -- the
        # ACTUAL #300 code under test, which is exercised through
        # BaseOperations.MoveUp/MoveDown/MoveToIndex and their generic
        # _GetObject (unaffected by either bug above), not through
        # DataNotebookOperations' own broken CRUD helpers.
        factory = target_sandbox.project.ServiceLocator.GetService(IRnGenericRecFactory)
        notebook_obj = target_sandbox.project.LangProject.ResearchNotebookOA
        parent = factory.Create()
        notebook_obj.RecordsOC.Add(parent)

        evidence["parent_has_RecordsOS"] = hasattr(parent, "RecordsOS")
        evidence["parent_has_SubRecordsOS"] = hasattr(parent, "SubRecordsOS")
        assert not hasattr(parent, "RecordsOS")
        assert hasattr(parent, "SubRecordsOS")

        s1 = factory.Create()
        parent.SubRecordsOS.Add(s1)
        s2 = factory.Create()
        parent.SubRecordsOS.Add(s2)
        s3 = factory.Create()
        parent.SubRecordsOS.Add(s3)

        pre_order = [r.Hvo for r in parent.SubRecordsOS]
        evidence["pre_order_hvo"] = pre_order
        assert pre_order == [s1.Hvo, s2.Hvo, s3.Hvo]

        notebook.MoveDown(parent, s1, 1)
        after_movedown = [r.Hvo for r in parent.SubRecordsOS]
        evidence["after_movedown_hvo"] = after_movedown
        assert after_movedown == [s2.Hvo, s1.Hvo, s3.Hvo]

        notebook.MoveUp(parent, s3, 2)
        after_moveup = [r.Hvo for r in parent.SubRecordsOS]
        evidence["after_moveup_hvo"] = after_moveup
        assert after_moveup == [s3.Hvo, s2.Hvo, s1.Hvo]

        notebook.MoveToIndex(parent, s2, 0)
        after_movetoindex = [r.Hvo for r in parent.SubRecordsOS]
        evidence["after_movetoindex_hvo"] = after_movetoindex
        assert after_movetoindex == [s2.Hvo, s3.Hvo, s1.Hvo]

        _write_evidence("300_datanotebook", evidence)


class TestIssue299ParagraphGetSequence:

    @pytest.mark.live_phase("ParagraphOperations", "reorder")
    def test_paragraph_reorder_and_sort_hit_text_paragraphsos(self, target_sandbox):
        texts = target_sandbox.Texts
        paragraphs = target_sandbox.Paragraphs
        evidence = {}

        text = texts.Create(f"{TEST_PREFIX}text_paras")
        try:
            p1 = paragraphs.Create(text, f"{TEST_PREFIX}para one.")
            p2 = paragraphs.Create(text, f"{TEST_PREFIX}para two.")
            p3 = paragraphs.Create(text, f"{TEST_PREFIX}para three.")

            pre_order = [p.Hvo for p in text.ContentsOA.ParagraphsOS]
            evidence["pre_order_hvo"] = pre_order
            assert pre_order == [p1.Hvo, p2.Hvo, p3.Hvo]

            paragraphs.MoveDown(text, p1, 1)
            after_movedown = [p.Hvo for p in text.ContentsOA.ParagraphsOS]
            evidence["after_movedown_hvo"] = after_movedown
            assert after_movedown == [p2.Hvo, p1.Hvo, p3.Hvo]

            paragraphs.MoveUp(text, p3, 2)
            after_moveup = [p.Hvo for p in text.ContentsOA.ParagraphsOS]
            evidence["after_moveup_hvo"] = after_moveup
            assert after_moveup == [p3.Hvo, p2.Hvo, p1.Hvo]

            paragraphs.MoveToIndex(text, p2, 0)
            after_movetoindex = [p.Hvo for p in text.ContentsOA.ParagraphsOS]
            evidence["after_movetoindex_hvo"] = after_movetoindex
            assert after_movetoindex == [p2.Hvo, p3.Hvo, p1.Hvo]

            count = paragraphs.Sort(text, key_func=lambda p: p.Hvo)
            after_sort = [p.Hvo for p in text.ContentsOA.ParagraphsOS]
            evidence["after_sort_hvo"] = after_sort
            evidence["sort_returned_count"] = count
            assert count == 3
            assert after_sort == sorted(after_sort)

            _write_evidence("299_paragraph", evidence)
        finally:
            try:
                texts.Delete(text)
            except Exception:
                pass


class TestIssue299SegmentGetSequence:

    @pytest.mark.live_phase("SegmentOperations", "reorder")
    def test_segment_reorder_hits_segmentsos_not_analysesrs(self, target_sandbox):
        from SIL.LCModel import IStTxtPara

        texts = target_sandbox.Texts
        paragraphs = target_sandbox.Paragraphs
        segments = target_sandbox.Segments
        evidence = {}

        text = texts.Create(f"{TEST_PREFIX}text_segs")
        try:
            paragraphs.Create(text, f"{TEST_PREFIX}sentence placeholder.")
            para = IStTxtPara(list(text.ContentsOA.ParagraphsOS)[0])

            evidence["parent_has_AnalysesRS"] = hasattr(para, "AnalysesRS")
            evidence["parent_has_SegmentsOS"] = hasattr(para, "SegmentsOS")
            assert not hasattr(para, "AnalysesRS")
            assert hasattr(para, "SegmentsOS")

            # NOTE: Paragraphs.Create's own placeholder sentence is parsed
            # into segment(s) automatically and asynchronously
            # (AnalysisAdjuster reacting to the Contents write; the exact
            # moment a materialized segment appears is not observed to be
            # stable relative to a pre-append snapshot), so SegmentsOS may
            # carry pre-existing entries ahead of the three this test
            # appends. AppendSentence always appends to the END of
            # SegmentsOS, so after three calls the LAST three entries are
            # guaranteed to be exactly s1, s2, s3 in that order --
            # base_n is computed AFTER the appends for that reason, not
            # from a pre-append baseline snapshot.
            s1 = segments.AppendSentence(para, f"{TEST_PREFIX}Segment one.")
            s2 = segments.AppendSentence(para, f"{TEST_PREFIX}Segment two.")
            s3 = segments.AppendSentence(para, f"{TEST_PREFIX}Segment three.")

            full = [s.Hvo for s in para.SegmentsOS]
            evidence["pre_order_hvo"] = full
            base_n = len(full) - 3
            pre_order = full[base_n:]
            assert pre_order == [s1.Hvo, s2.Hvo, s3.Hvo]

            segments.MoveDown(para, s1, 1)
            after_movedown = [s.Hvo for s in para.SegmentsOS][base_n:]
            evidence["after_movedown_hvo"] = after_movedown
            assert after_movedown == [s2.Hvo, s1.Hvo, s3.Hvo]

            # new_index is GLOBAL across the whole SegmentsOS sequence
            # (which still carries the baseline prefix), so target the
            # start of this test's own tail (base_n), not absolute 0 --
            # moving to absolute 0 would interleave with the pre-existing
            # baseline segments and defeat the tail-only comparison above.
            segments.MoveToIndex(para, s3, base_n)
            after_movetoindex = [s.Hvo for s in para.SegmentsOS][base_n:]
            evidence["after_movetoindex_hvo"] = after_movetoindex
            assert after_movetoindex == [s3.Hvo, s2.Hvo, s1.Hvo]

            _write_evidence("299_segment", evidence)
        finally:
            try:
                texts.Delete(text)
            except Exception:
                pass


class TestIssue299TextOperationsSequenceRemoved:

    @pytest.mark.live_phase("TextOperations", "reorder")
    def test_texts_sort_and_moveup_raise_notimplementederror_live(self, target_sandbox):
        texts = target_sandbox.Texts
        evidence = {}

        t1 = texts.Create(f"{TEST_PREFIX}text_a")
        t2 = texts.Create(f"{TEST_PREFIX}text_b")
        try:
            with pytest.raises(NotImplementedError) as sort_exc:
                texts.Sort(target_sandbox.project.LangProject, key_func=lambda t: 0)
            evidence["sort_raised"] = str(sort_exc.value)

            with pytest.raises(NotImplementedError) as moveup_exc:
                texts.MoveUp(target_sandbox.project.LangProject, t1, 1)
            evidence["moveup_raised"] = str(moveup_exc.value)

            _write_evidence("299_textoperations_removed", evidence)
        finally:
            for t in (t1, t2):
                try:
                    texts.Delete(t)
                except Exception:
                    pass


class TestIssue290ConstChartRowLabelNotesRoundTrip:

    @pytest.mark.live_phase("ConstChartRowOperations", "modify")
    def test_label_notes_create_set_clear_roundtrip(self, target_sandbox):
        charts = target_sandbox.ConstCharts
        rows = target_sandbox.ConstChartRows
        evidence = {}

        chart = charts.Create(f"{TEST_PREFIX}chart_labelnotes")
        try:
            row = rows.Create(
                chart,
                label=f"{TEST_PREFIX}Verse 1",
                notes=f"{TEST_PREFIX}initial notes",
            )
            pre_label = rows.GetLabel(row)
            pre_notes = rows.GetNotes(row)
            evidence["create_label"] = pre_label
            evidence["create_notes"] = pre_notes
            assert pre_label == f"{TEST_PREFIX}Verse 1"
            assert pre_notes == f"{TEST_PREFIX}initial notes"

            rows.SetLabel(row, f"{TEST_PREFIX}Verse 1 revised")
            rows.SetNotes(row, f"{TEST_PREFIX}revised notes")
            post_set_label = rows.GetLabel(row)
            post_set_notes = rows.GetNotes(row)
            evidence["post_set_label"] = post_set_label
            evidence["post_set_notes"] = post_set_notes
            assert post_set_label == f"{TEST_PREFIX}Verse 1 revised"
            assert post_set_notes == f"{TEST_PREFIX}revised notes"

            rows.SetLabel(row, "")
            rows.SetNotes(row, "")
            post_clear_label = rows.GetLabel(row)
            post_clear_notes = rows.GetNotes(row)
            evidence["post_clear_label"] = post_clear_label
            evidence["post_clear_notes"] = post_clear_notes
            assert post_clear_label == ""
            assert post_clear_notes == ""

            evidence["label_has_get_String"] = hasattr(row.Label, "get_String")
            evidence["label_has_set_String"] = hasattr(row.Label, "set_String")
            assert not hasattr(row.Label, "get_String")
            assert not hasattr(row.Label, "set_String")

            _write_evidence("290_constchartrow", evidence)
        finally:
            try:
                charts.Delete(chart)
            except Exception:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

