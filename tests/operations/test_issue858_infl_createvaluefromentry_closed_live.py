#
#   test_issue858_infl_createvaluefromentry_closed_live.py
#
#   Live gate for issue #858 _CreateValueFromEntry IFsClosedFeature guard.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def test_issue858_create_value_from_entry_rejects_non_closed_parent(target_sandbox):
    """Wrong-type parent_feature must raise FP_ParameterError, not CLR cast."""
    from types import SimpleNamespace

    from flexicon.code.FLExProject import FP_ParameterError

    project = target_sandbox
    infl_ops = project.InflectionFeatures
    complex_feat = infl_ops.Create(
        name=f"{TEST_PREFIX}person858",
        abbreviation="pers858",
        type="complex",
    )
    value_entry = SimpleNamespace(
        guid="e8f814f9-2345-4e2b-0b4e-000000000858",
        id="TEST_bad_parent858",
        term={"en": "x"},
        abbrev={"en": "x"},
        def_={},
    )
    try:
        with pytest.raises(FP_ParameterError, match="IFsClosedFeature parent"):
            infl_ops._CreateValueFromEntry(
                value_entry, complex_feat, set(), []
            )
    finally:
        try:
            infl_ops.FeatureDelete(complex_feat)
        except Exception:
            pass
