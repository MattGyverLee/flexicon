#
#   test_issue782_wfianalysis_delete_hvo_live.py
#
#   Live verification for issue #782 WfiAnalysisOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_782_"


def test_issue782_delete_removes_from_analysesoc_by_hvo(target_sandbox):
    """Delete removes an analysis when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    wf = project.Wordforms.Create(f"{TEST_PREFIX}wf")
    try:
        analysis = project.WfiAnalyses.Create(wf)
        assert wf.AnalysesOC.Count >= 1
        hvo = analysis.Hvo
        bare_view = project.Object(hvo)
        starting = wf.AnalysesOC.Count
        project.WfiAnalyses.Delete(bare_view)
        assert wf.AnalysesOC.Count == starting - 1
        assert not project.WfiAnalyses.Exists(wf, hvo)
    finally:
        project.Wordforms.Delete(wf)
