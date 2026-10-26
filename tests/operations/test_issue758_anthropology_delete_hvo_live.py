#
#   test_issue758_anthropology_delete_hvo_live.py
#
#   Live gate for issue #758 Delete HVO membership on anthropology hierarchy.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_758_"


@pytest.mark.requires_live_project
class TestIssue758AnthropologyDeleteHvoLive:
    """Delete must detach subitems when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("AnthropologyOperations", "delete")
    def test_delete_subitem_via_resolved_hvo(self, target_sandbox):
        anthro = target_sandbox.Anthropology
        parent_name = f"{TEST_PREFIX}parent"
        child_name = f"{TEST_PREFIX}child"

        parent = None
        child = None
        try:
            parent = anthro.Create(parent_name, "T758P")
            child = anthro.CreateSubitem(parent, child_name, "T758C")
            assert child is not None

            resolved = target_sandbox.Object(int(child.Hvo))
            anthro.Delete(resolved)

            subs = anthro.GetSubitems(parent, recursive=False)
            assert all(int(s.Hvo) != int(child.Hvo) for s in subs)
        finally:
            if child is not None:
                try:
                    anthro.Delete(child)
                except Exception:
                    pass
            if parent is not None:
                try:
                    anthro.Delete(parent)
                except Exception:
                    pass
