#
#   test_issue833_check_getlist_live.py
#
#   Live verification for issue #833 CheckOperations check-list accessor.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_833_"


def test_issue833_get_check_list_matches_created_checks(target_sandbox):
    """GetCheckList, GetAllCheckTypes, and DeleteCheckType share CheckListsOC."""
    project = target_sandbox
    checks = project.Checks
    name = f"{TEST_PREFIX}enum_delete"
    created = checks.CreateCheckType(name)
    try:
        check_list = checks.GetCheckList()
        assert check_list is not None

        listed = [c for c in checks.GetAllCheckTypes() if c.Hvo == created.Hvo]
        assert len(listed) == 1

        owner = project.Object(created.Hvo).Owner
        assert owner is not None
        assert owner.Hvo == check_list.Hvo

        checks.DeleteCheckType(created.Hvo)
        remaining = [c for c in checks.GetAllCheckTypes() if c.Hvo == created.Hvo]
        assert remaining == []
    finally:
        for c in checks.GetAllCheckTypes():
            if getattr(c, "Name", None) and str(c.Name) == name:
                checks.DeleteCheckType(c)
