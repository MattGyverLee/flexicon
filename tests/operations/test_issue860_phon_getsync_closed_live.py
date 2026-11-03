#
#   test_issue860_phon_getsync_closed_live.py
#
#   Live gate for issue #860 GetSyncableProperties closed-feature guard.
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


def test_issue860_get_sync_rejects_non_closed_feature_handle(target_sandbox):
    """Wrong-type feature input maps to FP_ParameterError, not raw cast noise."""
    project = target_sandbox
    phon = project.PhonFeatures
    features = list(phon.GetAll())
    assert features, "Target should expose at least one phonological feature"
    closed = features[0]
    values = list(phon.GetValues(closed))
    assert values, "Need a feature value to use as wrong-type stand-in"
    wrong_handle = values[0]

    with pytest.raises(FP_ParameterError) as exc:
        phon.GetSyncableProperties(wrong_handle)
    assert "IFsClosedFeature" in str(exc.value)
