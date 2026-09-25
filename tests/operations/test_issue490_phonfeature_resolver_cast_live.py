#
#   test_issue490_phonfeature_resolver_cast_live.py
#
#   Live gate for issue #490 PhonFeatureOperations HVO resolver cast.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_490_"


@pytest.mark.requires_live_project
class TestIssue490PhonFeatureNameHvoGate:
    """
    GetName resolves the feature via __ResolveObject and reads Name --
    subtype-only on IFsClosedFeature.
    """

    @pytest.mark.live_phase("PhonFeatureOperations", "read")
    def test_get_name_via_genuine_feature_hvo(self, target_sandbox):
        sandbox = target_sandbox
        feat_name = f"{TEST_PREFIX}Backness"
        feature = sandbox.PhonFeatures.Create(feat_name, "bk")
        try:
            hvo = feature.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(hvo), "Name"), (
                "precondition failed: Name reachable on bare ICmObject view "
                "-- re-derive the gate site"
            )

            name = sandbox.PhonFeatures.GetName(hvo)
            assert isinstance(name, str)
            assert TEST_PREFIX in name
        finally:
            sandbox.PhonFeatures.Delete(feature)
