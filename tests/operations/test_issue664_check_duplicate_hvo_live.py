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
    def test_duplicate_insert_after_raw_object_view(self, sena3_sandbox):
        chk_a = sena3_sandbox.Checks.CreateCheckType(f"{TEST_PREFIX}a")
        chk_b = sena3_sandbox.Checks.CreateCheckType(f"{TEST_PREFIX}b")
        chk_c = sena3_sandbox.Checks.CreateCheckType(f"{TEST_PREFIX}c")
        try:
            raw_mid = sena3_sandbox.Object(chk_b.Hvo)
            dup = sena3_sandbox.Checks.Duplicate(
                raw_mid, insert_after=True, deep=False
            )

            # No public accessor exists for the check list (the private
            # Checks._GetCheckList() is a stub that always returns None), so
            # read the owning list back from the LCM via the created item.
            from SIL.LCModel import ICmPossibilityList

            owner = sena3_sandbox.Object(chk_b.Hvo).Owner
            assert owner is not None
            check_list = ICmPossibilityList(owner)
            order = [p.Hvo for p in check_list.PossibilitiesOS]
            assert order.index(dup.Hvo) == order.index(chk_b.Hvo) + 1

            sena3_sandbox.Checks.DeleteCheckType(dup)
            sena3_sandbox.Checks.DeleteCheckType(chk_c)
            sena3_sandbox.Checks.DeleteCheckType(chk_b)
            sena3_sandbox.Checks.DeleteCheckType(chk_a)
        except Exception:
            for chk in (chk_a, chk_b, chk_c):
                try:
                    sena3_sandbox.Checks.DeleteCheckType(chk)
                except Exception:
                    pass
            raise
