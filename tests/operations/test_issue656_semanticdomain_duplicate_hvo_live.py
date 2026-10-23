#
#   test_issue656_semanticdomain_duplicate_hvo_live.py
#
#   Live verification for issue #656 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_656_"


class TestIssue656SemanticDomainDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("SemanticDomainOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        num_base = "65699"
        dom_a = target_sandbox.SemanticDomains.Create(
            f"{TEST_PREFIX}a", f"{num_base}.1"
        )
        dom_b = target_sandbox.SemanticDomains.Create(
            f"{TEST_PREFIX}b", f"{num_base}.2"
        )
        dom_c = target_sandbox.SemanticDomains.Create(
            f"{TEST_PREFIX}c", f"{num_base}.3"
        )
        try:
            raw_mid = target_sandbox.Object(dom_b.Hvo)
            dup = target_sandbox.SemanticDomains.Duplicate(
                raw_mid, insert_after=True, deep=False
            )
            try:
                domain_list = target_sandbox.lp.SemanticDomainListOA
                order = [d.Hvo for d in domain_list.PossibilitiesOS]
                assert order.index(dup.Hvo) == order.index(dom_b.Hvo) + 1
            finally:
                target_sandbox.SemanticDomains.Delete(dup)
        finally:
            target_sandbox.SemanticDomains.Delete(dom_c)
            target_sandbox.SemanticDomains.Delete(dom_b)
            target_sandbox.SemanticDomains.Delete(dom_a)
