#
#   test_issue710_datanotebook_location_hvo_live.py
#
#   Live verification for issue #710 DataNotebook location HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_710_"


def test_issue710_remove_location_after_hvo_refetch(target_sandbox):
    """RemoveLocation detaches location when caller holds Object(hvo) view."""
    project = target_sandbox
    op = project.DataNotebook
    loc_op = project.Location
    title = f"{TEST_PREFIX}location_hvo"
    record = op.Create(title)
    try:
        location = loc_op.Create(f"{TEST_PREFIX}site", "en")
        op.AddLocation(record, location)
        bare_location = project.Object(location.Hvo)
        op.RemoveLocation(record, bare_location)
        locations = list(op.GetLocations(record))
        assert all(loc.Hvo != location.Hvo for loc in locations)
    finally:
        found = op.Find(title)
        if found is not None:
            op.Delete(found)
