#
#   test_issue866_phon_getvalues_closed_live.py
#
#   Issue #866: GetValues rejects a feature value handle (not a closed
#   feature) with FP_ParameterError. Verified on target_sandbox.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

TEST_PREFIX = "TEST_"


@pytest.mark.requires_live_project
class TestIssue866Live:

    def test_get_values_rejects_value_handle_as_feature(self, target_sandbox):
        from flexicon.code.FLexProject import FP_ParameterError

        p = target_sandbox
        feat = p.PhonFeatures.Create(
            name=f"{TEST_PREFIX}feat866",
            abbreviation="f866",
        )
        existing_val = p.PhonFeatures.CreateValue(feat, f"{TEST_PREFIX}v866", "+")
        try:
            with pytest.raises(FP_ParameterError) as exc:
                list(p.PhonFeatures.GetValues(existing_val))
            assert "IFsClosedFeature" in str(exc.value)
        finally:
            try:
                p.PhonFeatures.DeleteValue(existing_val)
            except Exception:
                pass
            try:
                p.PhonFeatures.Delete(feat)
            except Exception:
                pass
