#
#   test_issue842_anthropology_researcher_hvo_live.py
#
#   Live verification for issue #842 Anthropology researcher HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_842_"


def test_issue842_remove_researcher_after_hvo_refetch(target_sandbox):
    """RemoveResearcher detaches person when caller holds Object(hvo) view."""
    project = target_sandbox
    anthro = project.Anthropology
    person_op = project.Person
    title = f"{TEST_PREFIX}researcher_hvo"
    item = anthro.Create(title)
    try:
        person = person_op.Create(f"{TEST_PREFIX}fieldworker")
        anthro.AddResearcher(item, person)
        bare_person = project.Object(person.Hvo)
        anthro.RemoveResearcher(item, bare_person)
        researchers = list(anthro.GetResearchers(item))
        assert all(p.Hvo != person.Hvo for p in researchers)
    finally:
        found = anthro.Find(title)
        if found is not None:
            anthro.Delete(found)
