#
#   test_issue760_semanticdomain_delete_hvo_live.py
#
#   Live gate for issue #760 Delete HVO membership on semantic domain hierarchy.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_760_"


@pytest.mark.requires_live_project
class TestIssue760SemanticDomainDeleteHvoLive:
    """Delete must detach subdomains when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("SemanticDomainOperations", "delete")
    def test_delete_subdomain_via_resolved_hvo(self, target_sandbox):
        domains = target_sandbox.SemanticDomains
        parent_number = "998.760"
        child_number = "998.760.1"
        parent_name = f"{TEST_PREFIX}parent"
        child_name = f"{TEST_PREFIX}child"

        parent = None
        child = None
        try:
            parent = domains.Create(parent_name, parent_number)
            child = domains.Create(child_name, child_number, parent=parent)
            assert child is not None

            resolved = target_sandbox.Object(int(child.Hvo))
            domains.Delete(resolved)

            subs = domains.GetSubdomains(parent, recursive=False)
            assert all(int(s.Hvo) != int(child.Hvo) for s in subs)
        finally:
            if child is not None:
                try:
                    domains.Delete(child)
                except Exception:
                    pass
            if parent is not None:
                try:
                    domains.Delete(parent)
                except Exception:
                    pass
