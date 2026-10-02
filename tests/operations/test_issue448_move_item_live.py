#
#   test_issue448_move_item_live.py
#
#   Live LCM gate for issue #448: MoveItem re-parents nested possibility
#   items without deleting them.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_448_"


@pytest.mark.live_phase("PossibilityListOperations", "write")
def test_move_pos_subcategory_to_top_and_back(target_sandbox):
    """
    Create a nested POS under TEST_ prefix, move to top level and back,
    re-read parent and GUID from the LCM after each move.
    """
    pl = target_sandbox.PossibilityLists
    pos_list = pl.FindList("Parts of Speech")
    assert pos_list is not None

    parent = pl.CreateItem(
        pos_list,
        f"{TEST_PREFIX}Parent",
        "en",
    )
    # CreateItem takes no abbreviation; set it separately.
    pl.SetItemAbbreviation(parent, f"{TEST_PREFIX}P", "en")
    child = pl.CreateItem(
        pos_list,
        f"{TEST_PREFIX}Child",
        "en",
        parent=parent,
    )
    # CreateItem takes no abbreviation; set it separately.
    pl.SetItemAbbreviation(child, f"{TEST_PREFIX}C", "en")
    child_guid = pl.GetItemGuid(child)

    try:
        assert pl.GetParentItem(child) is not None
        assert pl.GetDepth(child) == 1

        pl.MoveItem(child, None)
        assert pl.GetParentItem(child) is None
        assert pl.GetDepth(child) == 0
        assert pl.GetItemGuid(child) == child_guid

        pl.MoveItem(child, parent)
        assert pl.GetParentItem(child) is not None
        assert pl.GetItemGuid(child) == child_guid
        assert pl.GetDepth(child) == 1
    finally:
        for item in (child, parent):
            try:
                pl.DeleteItem(item)
            except Exception:
                pass


@pytest.mark.live_phase("PossibilityListOperations", "write")
def test_move_nested_semantic_domain_round_trip(sena3_sandbox):
    """Nested CmSemanticDomain (second subclass owner) moves without deletion."""
    pl = sena3_sandbox.PossibilityLists
    # List names are localized in Sena 3; reach the list structurally.
    sd_list = sena3_sandbox.lp.SemanticDomainListOA
    assert sd_list is not None

    parent = pl.CreateItem(sd_list, f"{TEST_PREFIX}SDParent", "en")
    child = pl.CreateItem(sd_list, f"{TEST_PREFIX}SDChild", "en", parent=parent)
    child_guid = pl.GetItemGuid(child)
    try:
        assert pl.GetParentItem(child) is not None
        pl.MoveItem(child, None)
        assert pl.GetParentItem(child) is None
        assert pl.GetItemGuid(child) == child_guid
        pl.MoveItem(child, parent)
        assert pl.GetParentItem(child) is not None
        assert pl.GetItemGuid(child) == child_guid
        # Already in place: must neither crash nor delete.
        pl.MoveItem(child, parent)
        assert pl.GetItemGuid(child) == child_guid
    finally:
        for item in (child, parent):
            try:
                pl.DeleteItem(item)
            except Exception:
                pass
