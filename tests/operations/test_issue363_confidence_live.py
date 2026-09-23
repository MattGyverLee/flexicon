#
#   test_issue363_confidence_live.py
#
#   Live read-only coverage for issue #363: GetAnalysesWithConfidence scans
#   notebook records via ConfidenceRA.
#
#   Copyright 2026
#

import pytest


@pytest.mark.requires_live_project
def test_get_analyses_with_confidence_returns_notebook_records(sena3_sandbox):
    project = sena3_sandbox
    levels = project.Confidence.GetAll()
    if not levels:
        pytest.skip("Sena 3 sandbox has no confidence levels")

    level = levels[0]
    records = project.Confidence.GetAnalysesWithConfidence(level)
    assert isinstance(records, list)
    for record in records:
        assert record.ConfidenceRA is not None
        assert record.ConfidenceRA.Hvo == level.Hvo


@pytest.mark.requires_live_project
def test_get_glosses_with_confidence_raises(sena3_sandbox):
    from flexicon.code.FLExProject import FP_ParameterError

    project = sena3_sandbox
    levels = project.Confidence.GetAll()
    if not levels:
        pytest.skip("Sena 3 sandbox has no confidence levels")

    with pytest.raises(FP_ParameterError, match="IWfiGloss"):
        project.Confidence.GetGlossesWithConfidence(levels[0])
