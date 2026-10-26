#
#   test_issue728_lexentry_donotpublish_hvo_live.py
#
#   Live verification for issue #728 LexEntry DoNotPublishInRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_728_"


def test_issue728_remove_donotpublish_after_hvo_refetch(target_sandbox):
    """RemoveDoNotPublishIn unlinks publication when caller holds Object(hvo) view."""
    project = target_sandbox
    ops = project.LexEntry
    pubs = list(project.Publications.GetAll())
    if not pubs:
        pytest.skip("Target has no publications to reference")

    publication = pubs[0]
    entry = ops.Create(f"{TEST_PREFIX}donotpub_hvo")
    try:
        ops.AddDoNotPublishIn(entry, publication)
        assert len(ops.GetDoNotPublishIn(entry)) == 1

        bare_pub = project.Object(publication.Hvo)
        ops.RemoveDoNotPublishIn(entry, bare_pub)
        assert len(ops.GetDoNotPublishIn(entry)) == 0
    finally:
        ops.Delete(entry)
