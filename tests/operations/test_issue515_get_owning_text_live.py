#
#   test_issue515_get_owning_text_live.py
#
#   Live verification for issue #515 GetOwningText owner chain.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_515_"


class TestIssue515GetOwningTextLive:
    """GetOwningText must resolve text from chart HVO and raw chart views."""

    @pytest.mark.live_phase("DiscourseOperations", "read")
    def test_get_owning_text_accepts_chart_hvo_and_raw_object(self, target_sandbox):
        name = f"{TEST_PREFIX}text"
        text = target_sandbox.Texts.Create(name)
        chart = target_sandbox.Discourse.CreateChart(text, f"{TEST_PREFIX}chart")
        raw = target_sandbox.Object(chart.Hvo)

        owner_hvo = target_sandbox.Discourse.GetOwningText(chart.Hvo)
        owner_raw = target_sandbox.Discourse.GetOwningText(raw)

        assert owner_hvo.Hvo == text.Hvo
        assert owner_raw.Hvo == text.Hvo

    @pytest.mark.live_phase("DiscourseOperations", "write")
    def test_chart_create_getall_duplicate_delete_roundtrip(self, target_sandbox):
        ops = target_sandbox.Discourse
        text = target_sandbox.Texts.Create(f"{TEST_PREFIX}roundtrip")
        chart = ops.CreateChart(text, f"{TEST_PREFIX}chart")
        assert sorted(c.Hvo for c in ops.GetAllCharts(text.Hvo)) == [chart.Hvo]

        dup = ops.Duplicate(chart.Hvo, deep=False)
        assert dup.Hvo != chart.Hvo
        assert ops.GetOwningText(dup.Hvo).Hvo == text.Hvo
        assert sorted(c.Hvo for c in ops.GetAllCharts(text.Hvo)) == sorted([chart.Hvo, dup.Hvo])

        ops.DeleteChart(dup.Hvo)
        ops.DeleteChart(chart.Hvo)
        assert list(ops.GetAllCharts(text.Hvo)) == []
