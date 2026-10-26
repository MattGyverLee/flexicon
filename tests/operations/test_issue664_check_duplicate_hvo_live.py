#
#   test_issue664_check_duplicate_hvo_live.py
#
#   Live verification for issue #664 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_664_"


class TestIssue664CheckDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("CheckOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        check_list = target_sandbox.Checks._GetCheckList()
        assert check_list is not None

        chk_a = target_sandbox.Checks.CreateCheckType(f"{TEST_PREFIX}a")
        chk_b = target_sandbox.Checks.CreateCheckType(f"{TEST_PREFIX}b")
        chk_c = target_sandbox.Checks.CreateCheckType(f"{TEST_PREFIX}c")
        try:
            raw_mid = target_sandbox.Object(chk_b.Hvo)
            dup = target_sandbox.Checks.Duplicate(
                raw_mid, insert_after=True, deep=False
            )

            order = [p.Hvo for p in check_list.PossibilitiesOS]
            assert order.index(dup.Hvo) == order.index(chk_b.Hvo) + 1

            target_sandbox.Checks.DeleteCheckType(dup)
            target_sandbox.Checks.DeleteCheckType(chk_c)
            target_sandbox.Checks.DeleteCheckType(chk_b)
            target_sandbox.Checks.DeleteCheckType(chk_a)
        except Exception:
            for chk in (chk_a, chk_b, chk_c):
                try:
                    target_sandbox.Checks.DeleteCheckType(chk)
                except Exception:
                    pass
            raise
