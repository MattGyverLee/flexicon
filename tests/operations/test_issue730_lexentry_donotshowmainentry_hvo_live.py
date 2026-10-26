#
#   test_issue730_lexentry_donotshowmainentry_hvo_live.py
#
#   Live verification for issue #730 LexEntry DoNotShowMainEntryInRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_730_"


def test_issue730_remove_donotshowmainentry_after_hvo_refetch(target_sandbox):
    """RemoveDoNotShowMainEntryIn unlinks publication when caller holds Object(hvo) view."""
    project = target_sandbox
    ops = project.LexEntry
    pubs = list(project.Publications.GetAll())
    if not pubs:
        pytest.skip("Target has no publications to reference")

    publication = pubs[0]
    entry = ops.Create(f"{TEST_PREFIX}donotshow_hvo")
    try:
        ops.AddDoNotShowMainEntryIn(entry, publication)
        assert len(ops.GetDoNotShowMainEntryIn(entry)) == 1

        bare_pub = project.Object(publication.Hvo)
        ops.RemoveDoNotShowMainEntryIn(entry, bare_pub)
        assert len(ops.GetDoNotShowMainEntryIn(entry)) == 0
    finally:
        ops.Delete(entry)
