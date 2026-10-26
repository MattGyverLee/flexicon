#
#   test_issue796_naturalclass_delete_hvo_live.py
#
#   Live gate for issue #796 Delete HVO membership on NaturalClassesOS.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_796_"


@pytest.mark.requires_live_project
class TestIssue796NaturalClassDeleteHvoLive:
    """Delete must remove the natural class when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("NaturalClassOperations", "delete")
    def test_delete_via_resolved_hvo(self, target_sandbox):
        nc_ops = target_sandbox.NaturalClasses
        name = f"{TEST_PREFIX}nc"
        abbrev = "T796"

        nc = None
        try:
            nc = nc_ops.Create(name, abbrev)
            assert nc is not None
            nc_hvo = int(nc.Hvo)

            resolved = target_sandbox.Object(nc_hvo)
            nc_ops.Delete(resolved)

            for remaining in nc_ops.GetAll():
                assert int(remaining.Hvo) != nc_hvo
            nc = None
        finally:
            if nc is not None:
                try:
                    nc_ops.Delete(nc)
                except Exception:
                    pass
