#
#   test_issue754_possibility_list_delete_hvo_live.py
#
#   Live gate for issue #754 DeleteItem HVO membership on possibility lists.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_754_"


@pytest.mark.requires_live_project
class TestIssue754PossibilityListDeleteHvoLive:
    """DeleteItem must detach nested items when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("PossibilityListOperations", "delete")
    def test_delete_nested_item_via_resolved_hvo(self, target_sandbox):
        lists = target_sandbox.PossibilityLists
        list_name = f"{TEST_PREFIX}genres"
        parent_name = f"{TEST_PREFIX}parent"
        child_name = f"{TEST_PREFIX}child"

        poss_list = None
        try:
            poss_list = lists.CreateList(list_name)
            parent = lists.CreateItem(poss_list, parent_name)
            child = lists.CreateItem(poss_list, child_name, parent=parent)
            assert child is not None

            resolved = target_sandbox.Object(int(child.Hvo))
            lists.DeleteItem(resolved)

            children = lists.GetSubitems(parent)
            assert all(int(c.Hvo) != int(child.Hvo) for c in children)
        finally:
            if poss_list is not None:
                try:
                    lists.DeleteList(poss_list)
                except Exception:
                    pass
