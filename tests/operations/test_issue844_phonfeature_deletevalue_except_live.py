#
#   test_issue844_phonfeature_deletevalue_except_live.py
#
#   Live verification for issue #844 DeleteValue error-path (no broad except).
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_844_"


def test_issue844_delete_value_raises_when_not_in_valuesoc(target_sandbox):
    """Second DeleteValue on the same HVO raises instead of silent no-op."""
    project = target_sandbox
    phon_ops = project.PhonFeatures
    feat = phon_ops.Create(f"{TEST_PREFIX}feat", "F")
    try:
        val = phon_ops.CreateValue(feat, f"{TEST_PREFIX}plus", "+")
        hvo = val.Hvo
        bare_view = project.Object(hvo)

        phon_ops.DeleteValue(bare_view)

        with pytest.raises(FP_ParameterError, match="not a member of ValuesOC"):
            phon_ops.DeleteValue(bare_view)
    finally:
        phon_ops.Delete(feat)
