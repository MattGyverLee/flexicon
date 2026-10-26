#
#   test_issue652_location_duplicate_hvo_live.py
#
#   Live verification for issue #652 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_652_"


class TestIssue652LocationDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("LocationOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        name_a = f"{TEST_PREFIX}a"
        name_b = f"{TEST_PREFIX}b"
        name_c = f"{TEST_PREFIX}c"
        loc_a = target_sandbox.Location.Create(name_a)
        loc_b = target_sandbox.Location.Create(name_b)
        loc_c = target_sandbox.Location.Create(name_c)
        try:
            raw_mid = target_sandbox.Object(loc_b.Hvo)
            dup = target_sandbox.Location.Duplicate(
                raw_mid, insert_after=True, deep=False
            )

            possibilities = target_sandbox.lp.LocationsOA.PossibilitiesOS
            order = [loc.Hvo for loc in possibilities]
            assert order.index(dup.Hvo) == order.index(loc_b.Hvo) + 1

            target_sandbox.Location.Delete(dup)
        finally:
            for loc in (loc_c, loc_b, loc_a):
                try:
                    target_sandbox.Location.Delete(loc)
                except Exception:
                    pass
