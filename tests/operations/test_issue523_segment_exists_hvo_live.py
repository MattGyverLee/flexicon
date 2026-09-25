#
#   test_issue523_segment_exists_hvo_live.py
#
#   Live verification for issue #523 SegmentOperations Exists HVO membership.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


class TestIssue523SegmentExistsHvoLive:
    """Exists must return True when segment is passed as raw Object(hvo)."""

    def test_exists_true_for_raw_object_hvo_view(self, target_sandbox):
        text = target_sandbox.Texts.Create("TEST_523_exists", "Hello world.")
        para = list(target_sandbox.Paragraphs.GetAll(text))[0]
        seg = list(target_sandbox.Segments.GetAll(para))[0]
        raw = target_sandbox.Object(seg.Hvo)

        assert target_sandbox.Segments.Exists(para, seg) is True
        assert target_sandbox.Segments.Exists(para, raw) is True
        assert target_sandbox.Segments.Exists(para, seg.Hvo) is True

    def test_exists_false_for_foreign_segment(self, target_sandbox):
        text = target_sandbox.Texts.Create("TEST_523_exists_neg", "One. Two.")
        paras = list(target_sandbox.Paragraphs.GetAll(text))
        assert len(paras) >= 2
        seg_para0 = list(target_sandbox.Segments.GetAll(paras[0]))[0]
        assert target_sandbox.Segments.Exists(paras[1], seg_para0) is False
