#
#   test_issue508_text_resolver_live.py
#
#   Live gate for issue #508 Paragraph/Discourse text resolver cast.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_508_"


class TestIssue508TextResolverHvoGate:
    """__GetTextObject must accept HVO ints and raw ICmObject views."""

    @pytest.mark.live_phase("ParagraphOperations", "add")
    def test_paragraph_create_accepts_text_hvo_and_raw_object(self, target_sandbox):
        name = f"{TEST_PREFIX}para_text"
        text = target_sandbox.Texts.Create(name)
        raw = target_sandbox.Object(text.Hvo)

        para_hvo = target_sandbox.Paragraphs.Create(text.Hvo, f"{TEST_PREFIX}via_hvo")
        assert para_hvo is not None

        para_raw = target_sandbox.Paragraphs.Create(raw, f"{TEST_PREFIX}via_raw")
        assert para_raw is not None

        assert target_sandbox.Paragraphs.GetText(para_hvo).strip().endswith("via_hvo")
        assert target_sandbox.Paragraphs.GetText(para_raw).strip().endswith("via_raw")

    @pytest.mark.live_phase("DiscourseOperations", "read")
    def test_discourse_get_all_charts_accepts_text_hvo_and_raw_object(self, target_sandbox):
        name = f"{TEST_PREFIX}disc_text"
        text = target_sandbox.Texts.Create(name)
        raw = target_sandbox.Object(text.Hvo)

        list(target_sandbox.Discourse.GetAllCharts(text.Hvo))
        list(target_sandbox.Discourse.GetAllCharts(raw))
