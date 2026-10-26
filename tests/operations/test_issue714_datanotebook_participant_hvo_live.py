#
#   test_issue714_datanotebook_participant_hvo_live.py
#
#   Live verification for issue #714 DataNotebook participant HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_714_"


def test_issue714_remove_participant_after_hvo_refetch(target_sandbox):
    """RemoveParticipant unlinks person when caller holds Object(hvo) view."""
    project = target_sandbox
    op = project.DataNotebook
    person_op = project.Person
    title = f"{TEST_PREFIX}participant_hvo"
    record = op.Create(title)
    try:
        person = person_op.Create(f"{TEST_PREFIX}consultant", "en")
        op.AddParticipant(record, person)
        bare_person = project.Object(person.Hvo)
        op.RemoveParticipant(record, bare_person)
        participants = list(op.GetParticipants(record))
        assert all(p.Hvo != person.Hvo for p in participants)
    finally:
        found = op.Find(title)
        if found is not None:
            op.Delete(found)
