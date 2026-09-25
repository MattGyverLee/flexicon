#
#   test_issue492_possibility_resolver_cast_live.py
#
#   Live gate for issue #492 PossibilityListOperations HVO resolver casts.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_492_"


@pytest.mark.requires_live_project
class TestIssue492PossibilityItemNameHvoGate:
    """
    GetItemName resolves the item via __ResolveItem and reads Name --
    subtype-only on ICmPossibility.
    """

    @pytest.mark.live_phase("PossibilityListOperations", "write")
    def test_get_item_name_via_genuine_item_hvo(self, target_sandbox):
        sandbox = target_sandbox
        pl = sandbox.PossibilityLists
        pos_list = pl.FindList("Parts of Speech")
        assert pos_list is not None

        item = pl.CreateItem(
            pos_list,
            f"{TEST_PREFIX}POS",
            "en",
            abbreviation=f"{TEST_PREFIX}P",
        )
        try:
            hvo = item.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(hvo), "Name"), (
                "precondition failed: Name reachable on bare ICmObject view "
                "-- re-derive the gate site"
            )

            name = pl.GetItemName(hvo)
            assert isinstance(name, str)
            assert TEST_PREFIX in name
        finally:
            pl.DeleteItem(item)


@pytest.mark.requires_live_project
class TestIssue492PossibilityListNameHvoGate:
    """
    GetListName resolves the list via __ResolveList and reads Name --
    subtype-only on ICmPossibilityList.
    """

    @pytest.mark.live_phase("PossibilityListOperations", "read")
    def test_get_list_name_via_genuine_list_hvo(self, target_sandbox):
        sandbox = target_sandbox
        pl = sandbox.PossibilityLists
        pos_list = pl.FindList("Parts of Speech")
        assert pos_list is not None

        hvo = pos_list.Hvo
        assert isinstance(hvo, int), (
            "test setup error: hvo must be a genuine Python int"
        )
        assert not hasattr(sandbox.Object(hvo), "Name"), (
            "precondition failed: Name reachable on bare ICmObject view "
            "-- re-derive the gate site"
        )

        name = pl.GetListName(hvo)
        assert isinstance(name, str)
        assert name == "Parts of Speech"
