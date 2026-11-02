#
#   test_issue720_lexsense_usagetype_hvo_live.py
#
#   Live verification for issue #720 LexSense UsageTypesRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_720_"


def _make_entry(project, suffix):
    entry = project.LexEntry.Create(f"{TEST_PREFIX}{suffix}")
    return entry


def test_issue720_remove_usage_type_after_hvo_refetch(sena3_sandbox):
    """RemoveUsageType unlinks usage when caller holds Object(hvo) view."""
    project = sena3_sandbox
    ops = project.Senses
    # Sena 3 carries these lists on LexDb (localized list names, so a lookup
    # by English list name finds nothing).
    plist = project.lexDB.UsageTypesOA
    assert plist is not None and plist.PossibilitiesOS.Count > 0
    usage = plist.PossibilitiesOS[0]
    entry = _make_entry(project, "usage_hvo")
    try:
        sense = ops.Create(entry, f"{TEST_PREFIX}g")
        ops.AddUsageType(sense, usage)
        assert len(ops.GetUsageTypes(sense)) == 1

        bare_usage = project.Object(usage.Hvo)
        ops.RemoveUsageType(sense, bare_usage)
        assert len(ops.GetUsageTypes(sense)) == 0
    finally:
        project.LexEntry.Delete(entry)
