#
#   test_issue722_lexsense_domaintype_hvo_live.py
#
#   Live verification for issue #722 LexSense DomainTypesRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_722_"


def _make_entry(project, suffix):
    entry = project.LexEntry.Create(f"{TEST_PREFIX}{suffix}")
    return entry


def test_issue722_remove_domain_type_after_hvo_refetch(target_sandbox):
    """RemoveDomainType unlinks domain type when caller holds Object(hvo) view."""
    project = target_sandbox
    ops = project.Senses
    domain_type = None
    for plist in project.PossibilityLists.GetAllLists():
        plist_name = (
            project.PossibilityLists.GetName(plist)
            if hasattr(project.PossibilityLists, "GetName")
            else str(plist.Name)
        )
        if plist_name == "Semantic Domains":
            items = list(project.PossibilityLists.GetItems(plist))
            if items:
                domain_type = items[0]
                break
    if domain_type is None:
        pytest.skip("Target has no semantic domain items for domain-type link test")
    entry = _make_entry(project, "domaintype_hvo")
    try:
        sense = ops.Create(entry, f"{TEST_PREFIX}g")
        ops.AddDomainType(sense, domain_type)
        assert len(ops.GetDomainTypes(sense)) == 1

        bare_domain_type = project.Object(domain_type.Hvo)
        ops.RemoveDomainType(sense, bare_domain_type)
        assert len(ops.GetDomainTypes(sense)) == 0
    finally:
        project.LexEntry.Delete(entry)
