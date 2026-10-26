#
#   test_issue662_possibilitylist_duplicate_hvo_live.py
#
#   Live verification for issue #662 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_662_"


class TestIssue662PossibilityListDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("PossibilityListOperations", "write")
    def test_duplicate_insert_after_raw_object_top_level(self, target_sandbox):
        pl = target_sandbox.PossibilityLists
        pos_list = pl.FindList("Parts of Speech")
        assert pos_list is not None

        item_a = pl.CreateItem(pos_list, f"{TEST_PREFIX}a", "en")
        item_b = pl.CreateItem(pos_list, f"{TEST_PREFIX}b", "en")
        item_c = pl.CreateItem(pos_list, f"{TEST_PREFIX}c", "en")
        try:
            raw_b = target_sandbox.Object(item_b.Hvo)
            dup = pl.Duplicate(raw_b, insert_after=True, deep=False)

            order = [item.Hvo for item in pos_list.PossibilitiesOS]
            assert order.index(dup.Hvo) == order.index(item_b.Hvo) + 1

            pl.DeleteItem(dup)
        finally:
            for item in (item_c, item_b, item_a):
                try:
                    pl.DeleteItem(item)
                except Exception:
                    pass

    @pytest.mark.live_phase("PossibilityListOperations", "write")
    def test_duplicate_insert_after_raw_object_nested(self, target_sandbox):
        pl = target_sandbox.PossibilityLists
        pos_list = pl.FindList("Parts of Speech")
        assert pos_list is not None

        parent = pl.CreateItem(pos_list, f"{TEST_PREFIX}parent", "en")
        child = pl.CreateItem(
            pos_list, f"{TEST_PREFIX}child", "en", parent=parent
        )
        try:
            raw_child = target_sandbox.Object(child.Hvo)
            dup = pl.Duplicate(raw_child, insert_after=True, deep=False)

            order = [item.Hvo for item in parent.SubPossibilitiesOS]
            assert order.index(dup.Hvo) == order.index(child.Hvo) + 1

            pl.DeleteItem(dup)
        finally:
            for item in (child, parent):
                try:
                    pl.DeleteItem(item)
                except Exception:
                    pass
