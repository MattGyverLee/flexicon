#
#   test_issue521_segment_get_owning_paragraph_live.py
#
#   Live verification for issue #521 GetOwningParagraph and MergeSegments gate.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_521_"


class TestIssue521GetOwningParagraphLive:
    """GetOwningParagraph must resolve paragraph from segment HVO and raw views."""

    @pytest.mark.live_phase("SegmentOperations", "read")
    def test_get_owning_paragraph_accepts_segment_hvo_and_raw_object(
        self, target_sandbox
    ):
        text = target_sandbox.Texts.Create(f"{TEST_PREFIX}text")
        para = target_sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}one. Two.")
        segments = list(target_sandbox.Segments.GetAll(para))
        assert len(segments) >= 1
        seg = segments[0]
        raw = target_sandbox.Object(seg.Hvo)

        owner_hvo = target_sandbox.Segments.GetOwningParagraph(seg.Hvo)
        owner_raw = target_sandbox.Segments.GetOwningParagraph(raw)

        assert owner_hvo.Hvo == para.Hvo
        assert owner_raw.Hvo == para.Hvo


class TestIssue521MergeSegmentsTypedOwnerLive:
    """MergeSegments must succeed when seg2 is passed as raw Object(hvo)."""

    @pytest.mark.live_phase("SegmentOperations", "modify")
    def test_merge_segments_mixed_segment_representations(self, target_sandbox):
        text = target_sandbox.Texts.Create(f"{TEST_PREFIX}merge")
        para = target_sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}Alpha. Beta.")
        segments = list(target_sandbox.Segments.GetAll(para))
        assert len(segments) >= 2, "need two segments to merge"
        seg1 = segments[0]
        seg2_raw = target_sandbox.Object(segments[1].Hvo)

        before = para.SegmentsOS.Count
        survivor = target_sandbox.Segments.MergeSegments(seg1, seg2_raw)
        assert survivor.Hvo == seg1.Hvo
        assert para.SegmentsOS.Count == before - 1
