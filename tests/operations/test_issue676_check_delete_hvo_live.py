#
#   test_issue676_check_delete_hvo_live.py
#
#   Live verification for issue #676 DeleteCheckType HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def test_issue676_delete_check_type_removes_by_hvo(target_project):
    """DeleteCheckType removes a custom check from PossibilitiesOS after cast handle."""
    project = target_project
    checks = project.Checks
    name = "TEST_676_delete_hvo"
    created = checks.CreateCheckType(name)
    try:
        hvo = created.Hvo
        checks.DeleteCheckType(hvo)
        remaining = [c for c in checks.GetAllCheckTypes() if c.Hvo == hvo]
        assert remaining == []
    finally:
        for c in checks.GetAllCheckTypes():
            if getattr(c, "Name", None) and str(c.Name) == name:
                checks.DeleteCheckType(c)
