#
#   test_issue788_paragraph_delete_hvo_live.py
#
#   Live verification for issue #788 ParagraphOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_788_"


def test_issue788_delete_removes_from_paragraphsos_by_hvo(target_sandbox):
    """Delete removes a paragraph when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    text = project.Texts.Create(f"{TEST_PREFIX}text")
    try:
        para = project.Paragraphs.Create(text, f"{TEST_PREFIX}para")
        st_text = project.Paragraphs._GetTypedOwner(para)
        assert st_text is not None
        starting = st_text.ParagraphsOS.Count
        hvo = para.Hvo
        bare_view = project.Object(hvo)
        project.Paragraphs.Delete(bare_view)
        assert st_text.ParagraphsOS.Count == starting - 1
        assert not any(int(p.Hvo) == int(hvo) for p in st_text.ParagraphsOS)
    finally:
        try:
            project.Texts.Delete(text)
        except Exception:
            pass
