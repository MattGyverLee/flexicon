#
#   test_issue762_pos_delete_hvo_live.py
#
#   Live gate for issue #762 Delete / RemoveSubcategory HVO membership.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_762_"


@pytest.mark.requires_live_project
class TestIssue762PosDeleteHvoLive:
    """Delete and RemoveSubcategory must detach when passed Object(hvo)."""

    @pytest.mark.live_phase("POSOperations", "delete")
    def test_delete_top_level_via_resolved_hvo(self, target_sandbox):
        pos_ops = target_sandbox.POS
        name = f"{TEST_PREFIX}top"

        created = None
        try:
            created = pos_ops.Create(name, "T762")
            assert created is not None

            resolved = target_sandbox.Object(int(created.Hvo))
            pos_ops.Delete(resolved)

            assert pos_ops.Find(name) is None
        finally:
            if created is not None and pos_ops.Find(name) is not None:
                try:
                    pos_ops.Delete(created)
                except Exception:
                    pass

    @pytest.mark.live_phase("POSOperations", "remove_subcategory")
    def test_remove_subcategory_via_resolved_hvo(self, target_sandbox):
        pos_ops = target_sandbox.POS
        parent_name = f"{TEST_PREFIX}parent"
        child_name = f"{TEST_PREFIX}sub"

        parent = None
        child = None
        try:
            parent = pos_ops.Create(parent_name, "T762P")
            child = pos_ops.AddSubcategory(parent, child_name, "T762C")
            assert child is not None

            resolved_parent = target_sandbox.Object(int(parent.Hvo))
            resolved_child = target_sandbox.Object(int(child.Hvo))
            pos_ops.RemoveSubcategory(resolved_parent, resolved_child)

            subs = pos_ops.GetSubcategories(parent)
            assert all(int(s.Hvo) != int(child.Hvo) for s in subs)
        finally:
            if child is not None:
                try:
                    pos_ops.RemoveSubcategory(parent, child)
                except Exception:
                    pass
            if parent is not None:
                try:
                    pos_ops.Delete(parent)
                except Exception:
                    pass
