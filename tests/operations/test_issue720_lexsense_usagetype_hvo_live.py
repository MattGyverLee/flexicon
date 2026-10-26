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


def test_issue720_remove_usage_type_after_hvo_refetch(target_sandbox):
    """RemoveUsageType unlinks usage when caller holds Object(hvo) view."""
    project = target_sandbox
    ops = project.Senses
    usage = None
    for plist in project.PossibilityLists.GetAllLists():
        plist_name = (
            project.PossibilityLists.GetName(plist)
            if hasattr(project.PossibilityLists, "GetName")
            else str(plist.Name)
        )
        if plist_name in ("Usages", "Usage Types"):
            items = list(project.PossibilityLists.GetItems(plist))
            if items:
                usage = items[0]
                break
    if usage is None:
        pytest.skip("Target has no usage types to reference")
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
