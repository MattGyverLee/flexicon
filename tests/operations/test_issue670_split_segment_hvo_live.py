#
#   test_issue670_split_segment_hvo_live.py
#
#   Live verification for issue #670 SplitSegment HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_670_"


class TestIssue670SplitSegmentHvoLive:
    """Split must insert after seg when passed as raw Object(hvo)."""

    @pytest.mark.live_phase("SegmentOperations", "modify")
    def test_split_inserts_after_raw_segment_in_segments_os(self, target_sandbox):
        text = target_sandbox.Texts.Create(f"{TEST_PREFIX}split")
        para = target_sandbox.Paragraphs.Create(
            text, f"{TEST_PREFIX}Alpha beta gamma."
        )
        segments = list(target_sandbox.Segments.GetAll(para))
        assert len(segments) >= 1, "need at least one segment to split"
        seg = segments[0]
        seg_hvo = seg.Hvo
        seg_raw = target_sandbox.Object(seg_hvo)
        offset = max(1, (seg.EndOffset - seg.BeginOffset) // 2)

        before = para.SegmentsOS.Count
        seg1, seg2 = target_sandbox.Segments.SplitSegment(seg_raw, offset)
        assert para.SegmentsOS.Count == before + 1
        hvos = [s.Hvo for s in para.SegmentsOS]
        assert seg1.Hvo == seg_hvo
        assert seg2.Hvo in hvos
        assert hvos.index(seg2.Hvo) == hvos.index(seg_hvo) + 1
