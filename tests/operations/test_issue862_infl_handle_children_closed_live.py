#
#   test_issue862_infl_handle_children_closed_live.py
#
#   Live gate for issue #862 _handle_entry_children IFsClosedFeature guard.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def test_issue862_handle_entry_children_rejects_non_closed_parent(target_sandbox):
    """Wrong-type created_feature must raise FP_ParameterError, not CLR cast."""
    from types import SimpleNamespace

    from flexicon.code.FLExProject import FP_ParameterError

    project = target_sandbox
    infl_ops = project.InflectionFeatures
    complex_feat = infl_ops.Create(
        name=f"{TEST_PREFIX}person862",
        abbreviation="pers862",
        type="complex",
    )
    entry = SimpleNamespace(children=[])
    try:
        with pytest.raises(FP_ParameterError, match="IFsClosedFeature parent"):
            infl_ops._handle_entry_children(
                entry, complex_feat, set(), [], None
            )
    finally:
        try:
            infl_ops.FeatureDelete(complex_feat)
        except Exception:
            pass
