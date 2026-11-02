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


def test_issue722_remove_domain_type_after_hvo_refetch(sena3_sandbox):
    """RemoveDomainType unlinks domain type when caller holds Object(hvo) view."""
    project = sena3_sandbox
    ops = project.Senses
    # Sena 3 carries these lists on LexDb (localized list names, so a lookup
    # by English list name finds nothing).
    plist = project.lexDB.DomainTypesOA
    assert plist is not None and plist.PossibilitiesOS.Count > 0
    domain_type = plist.PossibilitiesOS[0]
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
