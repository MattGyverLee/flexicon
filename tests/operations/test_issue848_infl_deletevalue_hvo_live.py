#
#   test_issue848_infl_deletevalue_hvo_live.py
#
#   Live verification for issue #848 InflectionFeatureOperations DeleteValue.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_848_"


def test_issue848_delete_value_removes_from_valuesoc_by_hvo(target_sandbox):
    """DeleteValue removes a value when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    infl_ops = project.InflectionFeatures
    feat = infl_ops.Create(f"{TEST_PREFIX}feat", "F", type="closed")
    try:
        plus = infl_ops.CreateValue(feat, f"{TEST_PREFIX}plus", "+")
        minus = infl_ops.CreateValue(feat, f"{TEST_PREFIX}minus", "-")
        hvo = minus.Hvo
        bare_view = project.Object(hvo)

        infl_ops.DeleteValue(bare_view)

        remaining = {int(v.Hvo) for v in infl_ops.FeatureGetValues(feat)}
        assert int(plus.Hvo) in remaining
        assert int(hvo) not in remaining
    finally:
        infl_ops.FeatureDelete(feat)
