#
#   test_issue868_infl_featuregetvalues_closed_live.py
#
#   Issue #868: FeatureGetValues rejects a feature value handle (not a
#   closed feature) with FP_ParameterError. Verified on target_sandbox.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

TEST_PREFIX = "TEST_"


@pytest.mark.requires_live_project
class TestIssue868Live:

    def test_feature_get_values_rejects_value_handle_as_feature(self, target_sandbox):
        from flexicon.code.FLexProject import FP_ParameterError

        p = target_sandbox
        feat = p.InflectionFeatures.Create(
            name=f"{TEST_PREFIX}feat868",
            abbreviation="f868",
        )
        existing_val = p.InflectionFeatures.CreateValue(
            feat, f"{TEST_PREFIX}v868", "1"
        )
        try:
            with pytest.raises(FP_ParameterError) as exc:
                p.InflectionFeatures.FeatureGetValues(existing_val)
            assert "IFsClosedFeature" in str(exc.value)
        finally:
            try:
                p.InflectionFeatures.DeleteValue(feat, existing_val)
            except Exception:
                pass
            try:
                p.InflectionFeatures.FeatureDelete(feat)
            except Exception:
                pass

    def test_feature_get_values_rejects_complex_feature(self, target_sandbox):
        from flexicon.code.FLexProject import FP_ParameterError

        p = target_sandbox
        complex_feat = p.InflectionFeatures.Create(
            name=f"{TEST_PREFIX}complex868",
            abbreviation="c868",
            type="complex",
        )
        try:
            with pytest.raises(FP_ParameterError) as exc:
                p.InflectionFeatures.FeatureGetValues(complex_feat)
            assert "IFsClosedFeature" in str(exc.value)
        finally:
            try:
                p.InflectionFeatures.FeatureDelete(complex_feat)
            except Exception:
                pass
