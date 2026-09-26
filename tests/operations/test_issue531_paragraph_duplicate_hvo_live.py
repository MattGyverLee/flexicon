#
#   test_issue531_paragraph_duplicate_hvo_live.py
#
#   Live verification for issue #531 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_531_"


class TestIssue531ParagraphDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("ParagraphOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        text = target_sandbox.Texts.Create(f"{TEST_PREFIX}text")
        p0 = target_sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}first")
        p1 = target_sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}second")
        p2 = target_sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}third")

        raw_mid = target_sandbox.Object(p1.Hvo)
        dup = target_sandbox.Paragraphs.Duplicate(
            raw_mid, insert_after=True, deep=False
        )

        order = [p.Hvo for p in target_sandbox.Paragraphs.GetAll(text)]
        assert order.index(dup.Hvo) == order.index(p1.Hvo) + 1

        target_sandbox.Paragraphs.Delete(dup)
        target_sandbox.Paragraphs.Delete(p2)
        target_sandbox.Paragraphs.Delete(p1)
        target_sandbox.Paragraphs.Delete(p0)
