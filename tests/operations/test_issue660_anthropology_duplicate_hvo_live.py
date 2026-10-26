#
#   test_issue660_anthropology_duplicate_hvo_live.py
#
#   Live verification for issue #660 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_660_"


class TestIssue660AnthropologyDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("AnthropologyOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        name_a = f"{TEST_PREFIX}a"
        name_b = f"{TEST_PREFIX}b"
        name_c = f"{TEST_PREFIX}c"
        item_a = target_sandbox.Anthropology.Create(name_a)
        item_b = target_sandbox.Anthropology.Create(name_b)
        item_c = target_sandbox.Anthropology.Create(name_c)
        try:
            raw_mid = target_sandbox.Object(item_b.Hvo)
            dup = target_sandbox.Anthropology.Duplicate(
                raw_mid, insert_after=True, deep=False
            )

            anthro_list = target_sandbox.lp.AnthroListOA
            assert anthro_list is not None
            possibilities = anthro_list.PossibilitiesOS
            order = [item.Hvo for item in possibilities]
            assert order.index(dup.Hvo) == order.index(item_b.Hvo) + 1

            target_sandbox.Anthropology.Delete(dup)
        finally:
            for item in (item_c, item_b, item_a):
                try:
                    target_sandbox.Anthropology.Delete(item)
                except Exception:
                    pass
