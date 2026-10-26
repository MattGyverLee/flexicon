#
#   test_issue708_datanotebook_researcher_hvo_live.py
#
#   Live verification for issue #708 DataNotebook researcher HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_708_"


def test_issue708_remove_researcher_after_hvo_refetch(target_sandbox):
    """RemoveResearcher detaches person when caller holds Object(hvo) view."""
    project = target_sandbox
    op = project.DataNotebook
    person_op = project.Person
    title = f"{TEST_PREFIX}researcher_hvo"
    record = op.Create(title)
    try:
        person = person_op.Create(f"{TEST_PREFIX}fieldworker")
        op.AddResearcher(record, person)
        bare_person = project.Object(person.Hvo)
        op.RemoveResearcher(record, bare_person)
        researchers = list(op.GetResearchers(record))
        assert all(p.Hvo != person.Hvo for p in researchers)
    finally:
        found = op.Find(title)
        if found is not None:
            op.Delete(found)
