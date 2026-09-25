#
#   test_issue519_paragraph_get_owning_text_live.py
#
#   Live verification for issue #519 GetOwningText owner chain.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_519_"


class TestIssue519GetOwningTextLive:
    """GetOwningText must resolve text from paragraph HVO and raw paragraph views."""

    @pytest.mark.live_phase("ParagraphOperations", "read")
    def test_get_owning_text_accepts_para_hvo_and_raw_object(self, target_sandbox):
        name = f"{TEST_PREFIX}text"
        text = target_sandbox.Texts.Create(name)
        para = target_sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}content")
        raw = target_sandbox.Object(para.Hvo)

        owner_hvo = target_sandbox.Paragraphs.GetOwningText(para.Hvo)
        owner_raw = target_sandbox.Paragraphs.GetOwningText(raw)

        assert owner_hvo.Hvo == text.Hvo
        assert owner_raw.Hvo == text.Hvo
