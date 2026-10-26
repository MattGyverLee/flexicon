#
#   test_issue668_possibility_item_duplicate_hvo_live.py
#
#   Live verification for issue #668 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_668_"


class TestIssue668PossibilityItemDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("PublicationOperations", "write")
    def test_publications_duplicate_insert_after_raw_object_view(self, target_sandbox):
        sandbox = target_sandbox
        pub_a = sandbox.Publications.Create(f"{TEST_PREFIX}a")
        pub_b = sandbox.Publications.Create(f"{TEST_PREFIX}b")
        pub_c = sandbox.Publications.Create(f"{TEST_PREFIX}c")
        dup = None
        try:
            raw_mid = sandbox.Object(pub_b.Hvo)
            dup = sandbox.Publications.Duplicate(raw_mid, insert_after=True, deep=False)

            pub_list = sandbox.project.lexDB.PublicationTypesOA.PossibilitiesOS
            order = [p.Hvo for p in pub_list]
            assert order.index(dup.Hvo) == order.index(pub_b.Hvo) + 1
        finally:
            if dup is not None:
                sandbox.Publications.Delete(dup)
            sandbox.Publications.Delete(pub_c)
            sandbox.Publications.Delete(pub_b)
            sandbox.Publications.Delete(pub_a)
