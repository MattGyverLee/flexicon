#
#   test_issue840_inflclass_delete_hvo_live.py
#
#   Live verification for issue #840 InflectionFeatureOperations InflectionClassDelete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_840_"


def _still_has_name(ops, pos, name):
    for ic in pos.InflectionClassesOC:
        if ops.InflectionClassGetName(ic) == name:
            return ic
    return None


def test_issue840_inflection_class_delete_by_hvo(target_project):
    """InflectionClassDelete removes a class after re-fetching by HVO."""
    project = target_project
    ops = project.InflectionFeatures
    pos_list = list(project.POS.GetAll())
    assert pos_list, "Target project needs at least one POS"
    pos = pos_list[0]
    name = f"{TEST_PREFIX}delete_hvo"
    ic = ops.InflectionClassCreate(name, pos=pos)
    try:
        hvo = ic.Hvo
        bare_view = project.Object(hvo)
        ops.InflectionClassDelete(bare_view)
        assert _still_has_name(ops, pos, name) is None
    finally:
        leftover = _still_has_name(ops, pos, name)
        if leftover is not None:
            ops.InflectionClassDelete(leftover)
