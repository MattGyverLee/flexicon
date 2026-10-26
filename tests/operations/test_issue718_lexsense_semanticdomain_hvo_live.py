#
#   test_issue718_lexsense_semanticdomain_hvo_live.py
#
#   Live verification for issue #718 LexSense SemanticDomainsRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_718_"


def _make_entry(project, suffix):
    entry = project.LexEntry.Create(f"{TEST_PREFIX}{suffix}")
    return entry


def test_issue718_remove_semantic_domain_after_hvo_refetch(target_sandbox):
    """RemoveSemanticDomain unlinks domain when caller holds Object(hvo) view."""
    project = target_sandbox
    ops = project.Senses
    domains = list(project.SemanticDomains.GetAll())
    if not domains:
        pytest.skip("Target has no semantic domains to reference")

    domain = domains[0]
    entry = _make_entry(project, "domain_hvo")
    try:
        sense = ops.Create(entry, f"{TEST_PREFIX}g")
        ops.AddSemanticDomain(sense, domain)
        assert len(ops.GetSemanticDomains(sense)) == 1

        bare_domain = project.Object(domain.Hvo)
        ops.RemoveSemanticDomain(sense, bare_domain)
        assert len(ops.GetSemanticDomains(sense)) == 0
    finally:
        project.LexEntry.Delete(entry)
