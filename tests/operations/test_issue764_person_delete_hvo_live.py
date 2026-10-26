#
#   test_issue764_person_delete_hvo_live.py
#
#   Live gate for issue #764 Delete HVO membership on PeopleOA.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_764_"


@pytest.mark.requires_live_project
class TestIssue764PersonDeleteHvoLive:
    """Delete must detach person when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("PersonOperations", "delete")
    def test_delete_person_via_resolved_hvo(self, target_sandbox):
        person_ops = target_sandbox.Person
        name = f"{TEST_PREFIX}someone"

        created = None
        try:
            created = person_ops.Create(name)
            assert created is not None

            resolved = target_sandbox.Object(int(created.Hvo))
            person_ops.Delete(resolved)

            assert person_ops.Find(name) is None
        finally:
            if created is not None:
                try:
                    person_ops.Delete(created)
                except Exception:
                    pass
