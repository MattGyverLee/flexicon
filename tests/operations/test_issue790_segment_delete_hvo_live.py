#
#   test_issue790_segment_delete_hvo_live.py
#
#   Live verification for issue #790 SegmentOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_790_"


def test_issue790_delete_removes_from_segmentsos_by_hvo(target_sandbox):
    """Delete removes a segment when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    text = project.Texts.Create(f"{TEST_PREFIX}text")
    try:
        para = project.Paragraphs.Create(text, f"{TEST_PREFIX}para")
        segment = project.Segments.AppendSentence(para, f"{TEST_PREFIX}seg.")
        st_para = project.Segments._GetTypedOwner(segment)
        assert st_para is not None
        starting = st_para.SegmentsOS.Count
        hvo = segment.Hvo
        bare_view = project.Object(hvo)
        project.Segments.Delete(bare_view)
        assert st_para.SegmentsOS.Count == starting - 1
        assert not any(int(s.Hvo) == int(hvo) for s in st_para.SegmentsOS)
    finally:
        try:
            project.Texts.Delete(text)
        except Exception:
            pass
