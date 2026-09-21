#
#   test_352_compareto_live.py
#
#   Live regression coverage for the _CompareValues follow-up to issue
#   #352: eight CompareTo methods called FLExProject._CompareValues,
#   which does not exist (AttributeError on every compare). All eight
#   now compare inline. Each test compares an object with itself and
#   expects no differences.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

pytestmark = pytest.mark.requires_live_project


class Test352CompareToSelfEquality:
    @pytest.mark.live_phase("TextOperations", "read")
    def test_text_compareto(self, target_sandbox):
        texts = target_sandbox.Texts
        text = texts.Create("TEST_352 compare")
        try:
            is_diff, diffs = texts.CompareTo(text, text)
            assert not is_diff, diffs
        finally:
            texts.Delete(text)

    @pytest.mark.live_phase("ParagraphOperations", "read")
    def test_paragraph_compareto(self, target_sandbox):
        texts = target_sandbox.Texts
        paras = target_sandbox.Paragraphs
        text = texts.Create("TEST_352 compare para")
        try:
            para = paras.Create(text, "TEST_352 paragraph content")
            is_diff, diffs = paras.CompareTo(para, para)
            assert not is_diff, diffs
        finally:
            texts.Delete(text)

    @pytest.mark.live_phase("DiscourseOperations", "read")
    def test_discourse_compareto(self, target_sandbox):
        charts = target_sandbox.ConstCharts
        disc = target_sandbox.Discourse
        chart = charts.Create("TEST_352 compare chart")
        try:
            is_diff, diffs = disc.CompareTo(chart, chart)
            assert not is_diff, diffs
        finally:
            charts.Delete(chart)

    @pytest.mark.live_phase("WordformOperations", "read")
    def test_wordform_chain_compareto(self, target_sandbox):
        wfs = target_sandbox.Wordforms
        wf = wfs.Create("TEST_352wf")
        try:
            is_diff, diffs = wfs.CompareTo(wf, wf)
            assert not is_diff, diffs
            analyses = target_sandbox.WfiAnalyses
            analysis = analyses.Create(wf)
            is_diff, diffs = analyses.CompareTo(analysis, analysis)
            assert not is_diff, diffs
            glosses = target_sandbox.WfiGlosses
            gloss = glosses.Create(analysis, "TEST_352 gloss")
            is_diff, diffs = glosses.CompareTo(gloss, gloss)
            assert not is_diff, diffs
            bundles = target_sandbox.WfiMorphBundles
            bundle = bundles.Create(analysis)
            is_diff, diffs = bundles.CompareTo(bundle, bundle)
            assert not is_diff, diffs
        finally:
            wfs.Delete(wf)

    @pytest.mark.live_phase("SegmentOperations", "read")
    def test_segment_compareto_if_any(self, target_sandbox):
        texts = target_sandbox.Texts
        paras = target_sandbox.Paragraphs
        segs = target_sandbox.Segments
        text = texts.Create("TEST_352 compare seg")
        try:
            para = paras.Create(text, "TEST_352 segment content")
            segments = list(segs.GetAll(para))
            if not segments:
                pytest.skip("No segments produced on Target; Segment CompareTo shape-verified by code review")
            is_diff, diffs = segs.CompareTo(segments[0], segments[0])
            assert not is_diff, diffs
        finally:
            texts.Delete(text)
