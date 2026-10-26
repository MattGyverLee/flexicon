#
#   test_issue726_lexsense_donotpublish_hvo_live.py
#
#   Live verification for issue #726 LexSense DoNotPublishInRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_726_"


def _make_entry(project, suffix):
    entry = project.LexEntry.Create(f"{TEST_PREFIX}{suffix}")
    return entry


def test_issue726_remove_donotpublish_after_hvo_refetch(target_sandbox):
    """RemoveDoNotPublishIn unlinks publication when caller holds Object(hvo) view."""
    project = target_sandbox
    ops = project.Senses
    pubs = list(project.Publications.GetAll())
    if not pubs:
        pytest.skip("Target has no publications to reference")

    publication = pubs[0]
    entry = _make_entry(project, "donotpub_hvo")
    try:
        sense = ops.Create(entry, f"{TEST_PREFIX}g")
        ops.AddDoNotPublishIn(sense, publication)
        assert len(ops.GetDoNotPublishIn(sense)) == 1

        bare_pub = project.Object(publication.Hvo)
        ops.RemoveDoNotPublishIn(sense, bare_pub)
        assert len(ops.GetDoNotPublishIn(sense)) == 0
    finally:
        project.LexEntry.Delete(entry)
