#
#   test_issue870_phon_applyvalues_closed_live.py
#
#   Live gate for issue #870 __ApplyValues closed-feature guard (exercised
#   via ApplySyncableProperties value co-create branch on target_sandbox).
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


def test_issue870_apply_values_branch_rejects_wrong_handle(target_sandbox):
    """Value-sync branch maps wrong-type input to FP_ParameterError."""
    project = target_sandbox
    phon = project.PhonFeatures
    features = list(phon.GetAll())
    assert features, "Target should expose at least one phonological feature"
    closed = features[0]
    values = list(phon.GetValues(closed))
    assert values, "Need a feature value to use as wrong-type stand-in"
    wrong_handle = values[0]

    with pytest.raises(FP_ParameterError) as exc:
        phon.ApplySyncableProperties(
            wrong_handle,
            {"Values": [{"Name": {"en": "TEST_wrong_branch"}}]},
        )
    assert "IFsClosedFeature" in str(exc.value)
