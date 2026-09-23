#
#   test_issue362_person_gsp_live.py
#
#   Live read-only coverage for issue #362: GetSyncableProperties on every person.
#
#   Copyright 2026
#

import pytest


@pytest.mark.requires_live_project
def test_get_syncable_properties_on_all_people(sena3_sandbox):
    project = sena3_sandbox
    people = project.Person.GetAll()
    assert people, "expected at least one person in Sena 3 sandbox"

    for person in people:
        props = project.Person.GetSyncableProperties(person)
        assert isinstance(props, dict)
        assert "Name" in props
        assert "Languages" not in props
