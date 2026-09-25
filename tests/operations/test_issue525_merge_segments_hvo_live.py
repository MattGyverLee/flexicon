#
#   test_issue525_merge_segments_hvo_live.py
#
#   Live verification for issue #525 MergeSegments HVO index/remove.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_525_"


class TestIssue525MergeSegmentsHvoLive:
    """Merge must drop seg2 when passed as raw Object(hvo)."""

    @pytest.mark.live_phase("SegmentOperations", "modify")
    def test_merge_removes_raw_seg2_from_segments_os(self, target_sandbox):
        text = target_sandbox.Texts.Create(f"{TEST_PREFIX}merge")
        para = target_sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}Alpha. Beta.")
        segments = list(target_sandbox.Segments.GetAll(para))
        assert len(segments) >= 2, "need two segments to merge"
        seg1 = segments[0]
        seg2_hvo = segments[1].Hvo
        seg2_raw = target_sandbox.Object(seg2_hvo)

        before = para.SegmentsOS.Count
        survivor = target_sandbox.Segments.MergeSegments(seg1, seg2_raw)
        assert survivor.Hvo == seg1.Hvo
        assert para.SegmentsOS.Count == before - 1
        remaining_hvos = {seg.Hvo for seg in para.SegmentsOS}
        assert seg2_hvo not in remaining_hvos
