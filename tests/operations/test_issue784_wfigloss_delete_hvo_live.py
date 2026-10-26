#
#   test_issue784_wfigloss_delete_hvo_live.py
#
#   Live verification for issue #784 WfiGlossOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_784_"


def test_issue784_delete_removes_from_meaningsoc_by_hvo(target_sandbox):
    """Delete removes a gloss when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    wf = project.Wordforms.Create(f"{TEST_PREFIX}wf")
    try:
        analysis = project.WfiAnalyses.Create(wf)
        gloss = project.WfiGlosses.Create(analysis, f"{TEST_PREFIX}gloss")
        assert analysis.MeaningsOC.Count >= 1
        hvo = gloss.Hvo
        bare_view = project.Object(hvo)
        starting = analysis.MeaningsOC.Count
        project.WfiGlosses.Delete(bare_view)
        assert analysis.MeaningsOC.Count == starting - 1
        assert not any(int(g.Hvo) == int(hvo) for g in analysis.MeaningsOC)
    finally:
        project.Wordforms.Delete(wf)
