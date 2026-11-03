#
#   test_issue864_phon_handle_children_closed_live.py
#
#   Live gate for issue #864 _handle_entry_children IFsClosedFeature guard.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def test_issue864_handle_entry_children_rejects_non_closed_parent(target_sandbox):
    """Wrong-type created_feature must raise FP_ParameterError, not CLR cast."""
    from types import SimpleNamespace

    from flexicon.code.FLExProject import FP_ParameterError

    project = target_sandbox
    infl_ops = project.InflectionFeatures
    phon_ops = project.PhonFeatures
    complex_feat = infl_ops.Create(
        name=f"{TEST_PREFIX}person864",
        abbreviation="pers864",
        type="complex",
    )
    entry = SimpleNamespace(children=[])
    try:
        with pytest.raises(FP_ParameterError, match="IFsClosedFeature parent"):
            phon_ops._handle_entry_children(
                entry, complex_feat, set(), [], None
            )
    finally:
        try:
            infl_ops.FeatureDelete(complex_feat)
        except Exception:
            pass
