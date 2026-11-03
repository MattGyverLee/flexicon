#
#   test_issue856_phon_createvaluefromentry_closed_live.py
#
#   Live gate for issue #856 _CreateValueFromEntry IFsClosedFeature guard.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def test_issue856_create_value_from_entry_rejects_non_closed_parent(target_sandbox):
    """Wrong-type parent_feature must raise FP_ParameterError, not CLR cast."""
    project = target_sandbox
    phon_ops = project.phonFeatureOps
    # MsFeatureSystem complex feature (no ValuesOC) as wrong parent shape.
    ms = project.lp.MsFeatureSystemOA
    complex_parent = None
    for raw in ms.FeaturesOC:
        if raw.ClassName == "FsComplexFeature":
            complex_parent = raw
            break
    if complex_parent is None:
        pytest.skip("Target has no FsComplexFeature for negative control")

    from types import SimpleNamespace

    value_entry = SimpleNamespace(
        guid="d7f713e8-1234-4d1a-9a3d-000000000099",
        id="TEST_bad_parent",
        term={"en": "x"},
        abbrev={"en": "x"},
        def_={},
    )

    from flexicon.code.FLExProject import FP_ParameterError

    with pytest.raises(FP_ParameterError, match="IFsClosedFeature parent"):
        phon_ops._CreateValueFromEntry(
            value_entry, complex_parent, set(), []
        )
