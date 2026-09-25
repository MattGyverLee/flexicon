#
#   test_issue465_segment_resolver_cast_live.py
#
#   Live gate for issue #465 SegmentOperations HVO resolver casts.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_465_"


@pytest.mark.requires_live_project
class TestIssue465SegmentAnalysesHvoGate:
    """
    GetAnalyses resolves the segment via __GetSegmentObject and reads
    AnalysesRS -- subtype-only on ISegment.
    """

    @pytest.mark.live_phase("SegmentOperations", "read")
    def test_get_analyses_via_genuine_segment_hvo(self, target_sandbox):
        sandbox = target_sandbox
        text = sandbox.Texts.Create(f"{TEST_PREFIX}text")
        try:
            para = sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}content for segments")
            segments = list(sandbox.Segments.GetAll(para))
            if not segments:
                pytest.skip(
                    "No segments on Target paragraph; cannot derive segment HVO gate"
                )
            segment = segments[0]
            hvo = segment.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(hvo), "AnalysesRS"), (
                "precondition failed: AnalysesRS reachable on bare ICmObject view "
                "-- re-derive the gate site"
            )

            analyses = sandbox.Segments.GetAnalyses(hvo)
            assert isinstance(analyses, list)
        finally:
            sandbox.Texts.Delete(text)
