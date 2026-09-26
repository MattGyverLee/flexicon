#
#   test_issue535_naturalclass_duplicate_hvo_live.py
#
#   Live verification for issue #535 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_535_"


class TestIssue535NaturalClassDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("NaturalClassOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        nc_ops = target_sandbox.NaturalClasses
        nc0 = nc_ops.Create(f"{TEST_PREFIX}a", f"{TEST_PREFIX}A")
        nc1 = nc_ops.Create(f"{TEST_PREFIX}b", f"{TEST_PREFIX}B")
        nc2 = nc_ops.Create(f"{TEST_PREFIX}c", f"{TEST_PREFIX}C")

        raw_mid = target_sandbox.Object(nc1.Hvo)
        dup = nc_ops.Duplicate(raw_mid, insert_after=True, deep=False)

        order = [nc.Hvo for nc in nc_ops.GetAll()]
        assert order.index(dup.Hvo) == order.index(nc1.Hvo) + 1

        nc_ops.Delete(dup)
        nc_ops.Delete(nc2)
        nc_ops.Delete(nc1)
        nc_ops.Delete(nc0)
