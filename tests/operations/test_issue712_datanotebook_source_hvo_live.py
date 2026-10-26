#
#   test_issue712_datanotebook_source_hvo_live.py
#
#   Live verification for issue #712 DataNotebook source HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_712_"


def test_issue712_remove_source_after_hvo_refetch(target_sandbox):
    """RemoveSource detaches source when caller holds Object(hvo) view."""
    project = target_sandbox
    op = project.DataNotebook
    person_op = project.Person
    title = f"{TEST_PREFIX}source_hvo"
    record = op.Create(title)
    try:
        source = person_op.Create(f"{TEST_PREFIX}informant", "en")
        op.AddSource(record, source)
        bare_source = project.Object(source.Hvo)
        op.RemoveSource(record, bare_source)
        sources = list(op.GetSources(record))
        assert all(src.Hvo != source.Hvo for src in sources)
    finally:
        found = op.Find(title)
        if found is not None:
            op.Delete(found)
