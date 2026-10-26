#
#   test_issue732_example_donotpublish_hvo_live.py
#
#   Live verification for issue #732 Example DoNotPublishInRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_732_"


def test_issue732_remove_donotpublish_after_hvo_refetch(target_sandbox):
    """RemoveDoNotPublishIn unlinks publication when caller holds Object(hvo) view."""
    project = target_sandbox
    pubs = list(project.Publications.GetAll())
    if not pubs:
        pytest.skip("Target has no publications to reference")

    publication = pubs[0]
    entry = project.LexEntry.Create(f"{TEST_PREFIX}entry")
    try:
        sense = project.Senses.Create(entry, f"{TEST_PREFIX}sense")
        example = project.Examples.Create(sense, f"{TEST_PREFIX}ex")
        project.Examples.AddDoNotPublishIn(example, publication)
        assert len(project.Examples.GetDoNotPublishIn(example)) == 1

        bare_pub = project.Object(publication.Hvo)
        project.Examples.RemoveDoNotPublishIn(example, bare_pub)
        assert len(project.Examples.GetDoNotPublishIn(example)) == 0
    finally:
        project.LexEntry.Delete(entry)
