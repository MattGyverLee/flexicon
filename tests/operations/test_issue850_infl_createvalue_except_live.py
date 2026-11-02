#
#   test_issue850_infl_createvalue_except_live.py
#
#   Issue #850: CreateValue on a complex inflection feature raises
#   FP_ParameterError (not a silent success). Verified on target_sandbox.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

TEST_PREFIX = "TEST_"


@pytest.mark.requires_live_project
class TestIssue850Live:

    def test_create_value_rejects_complex_feature(self, target_sandbox):
        from flexicon.code.FLexProject import FP_ParameterError

        p = target_sandbox
        complex_feat = p.InflectionFeatures.Create(
            name=f"{TEST_PREFIX}person850",
            abbreviation="pers850",
            type="complex",
        )
        try:
            with pytest.raises(FP_ParameterError) as exc:
                p.InflectionFeatures.CreateValue(complex_feat, "first", "1")
            assert "IFsClosedFeature" in str(exc.value)
        finally:
            try:
                p.InflectionFeatures.FeatureDelete(complex_feat)
            except Exception:
                pass
