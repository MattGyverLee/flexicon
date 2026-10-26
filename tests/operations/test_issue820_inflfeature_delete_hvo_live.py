#
#   test_issue820_inflfeature_delete_hvo_live.py
#
#   Live verification for issue #820 InflectionFeatureOperations FeatureDelete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_820_"


def test_issue820_feature_delete_by_hvo(target_project):
    """FeatureDelete removes a feature after re-fetching by HVO."""
    project = target_project
    ops = project.InflectionFeatures
    name = f"{TEST_PREFIX}delete_hvo"
    feature = ops.FeatureCreate(name, "complex")
    try:
        hvo = feature.Hvo
        bare_view = project.Object(hvo)
        ops.FeatureDelete(bare_view)
        assert ops.Find(name) is None
    finally:
        found = ops.Find(name)
        if found is not None:
            ops.FeatureDelete(found)
