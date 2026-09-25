#
#   test_issue517_paragraph_duplicate_parent_live.py
#
#   Live verification for issue #517 Duplicate parent-text resolution.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_517_"


class TestIssue517ParagraphDuplicateParentLive:
    """Duplicate must attach to the same text for HVO and raw paragraph views."""

    @pytest.mark.live_phase("ParagraphOperations", "write")
    def test_duplicate_accepts_para_hvo_and_raw_object(self, target_sandbox):
        name = f"{TEST_PREFIX}text"
        text = target_sandbox.Texts.Create(name)
        para = target_sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}para body")
        raw = target_sandbox.Object(para.Hvo)

        dup_hvo = target_sandbox.Paragraphs.Duplicate(para.Hvo, insert_after=True)
        dup_raw = target_sandbox.Paragraphs.Duplicate(raw, insert_after=True)

        paras = list(target_sandbox.Paragraphs.GetAll(text))
        dup_hvos = {dup_hvo.Hvo, dup_raw.Hvo}
        assert dup_hvos.issubset({p.Hvo for p in paras})
        assert len(paras) >= 3

        target_sandbox.Paragraphs.Delete(dup_hvo)
        target_sandbox.Paragraphs.Delete(dup_raw)
        target_sandbox.Paragraphs.Delete(para)
