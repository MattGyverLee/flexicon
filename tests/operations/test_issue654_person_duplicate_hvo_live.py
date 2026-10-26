#
#   test_issue654_person_duplicate_hvo_live.py
#
#   Live verification for issue #654 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_654_"


class TestIssue654PersonDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("PersonOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        name_a = f"{TEST_PREFIX}a"
        name_b = f"{TEST_PREFIX}b"
        name_c = f"{TEST_PREFIX}c"
        person_a = target_sandbox.Person.Create(name_a)
        person_b = target_sandbox.Person.Create(name_b)
        person_c = target_sandbox.Person.Create(name_c)
        try:
            raw_mid = target_sandbox.Object(person_b.Hvo)
            dup = target_sandbox.Person.Duplicate(
                raw_mid, insert_after=True, deep=False
            )

            possibilities = target_sandbox.lp.PeopleOA.PossibilitiesOS
            order = [person.Hvo for person in possibilities]
            assert order.index(dup.Hvo) == order.index(person_b.Hvo) + 1

            target_sandbox.Person.Delete(dup)
        finally:
            for person in (person_c, person_b, person_a):
                try:
                    target_sandbox.Person.Delete(person)
                except Exception:
                    pass
