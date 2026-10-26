#
#   test_issue756_location_delete_hvo_live.py
#
#   Live gate for issue #756 Delete HVO membership on location hierarchy.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_756_"


@pytest.mark.requires_live_project
class TestIssue756LocationDeleteHvoLive:
    """Delete must detach nested locations when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("LocationOperations", "delete")
    def test_delete_nested_location_via_resolved_hvo(self, target_sandbox):
        loc_ops = target_sandbox.Location
        parent_name = f"{TEST_PREFIX}region"
        child_name = f"{TEST_PREFIX}town"

        parent = None
        child = None
        try:
            parent = loc_ops.Create(parent_name, "en")
            child = loc_ops.Create(child_name, "en", parent=parent)
            assert child is not None

            resolved = target_sandbox.Object(int(child.Hvo))
            loc_ops.Delete(resolved)

            subs = loc_ops.GetSublocations(parent, recursive=False)
            assert all(int(s.Hvo) != int(child.Hvo) for s in subs)
        finally:
            if child is not None:
                try:
                    loc_ops.Delete(child)
                except Exception:
                    pass
            if parent is not None:
                try:
                    loc_ops.Delete(parent)
                except Exception:
                    pass
