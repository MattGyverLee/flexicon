#
#   test_issue502_wfigloss_analysis_resolver_cast_live.py
#
#   Live gate for issue #502 WfiGlossOperations analysis HVO resolver cast.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


@pytest.mark.requires_live_project
class TestIssue502WfiGlossGetCountHvoGate:
    """
    GetCount resolves via __ResolveAnalysis and reads MeaningsOC.Count --
    subtype-only on IWfiAnalysis.
    """

    @pytest.mark.live_phase("WfiGlossOperations", "read")
    def test_get_count_via_genuine_analysis_hvo(self, target_sandbox):
        sandbox = target_sandbox
        wf = sandbox.Wordforms.Create("TEST_issue502_wordform")
        try:
            analysis = sandbox.WfiAnalyses.Create(wf)
            gloss = sandbox.WfiGlosses.Create(analysis, "TEST_issue502_gloss")
            try:
                hvo = analysis.Hvo
                assert isinstance(hvo, int), (
                    "test setup error: hvo must be a genuine Python int"
                )
                bare = sandbox.Object(hvo)
                assert not hasattr(bare, "MeaningsOC"), (
                    "precondition failed: MeaningsOC reachable on bare "
                    "ICmObject view -- re-derive the gate site"
                )

                by_obj = sandbox.WfiGlosses.GetCount(analysis)
                by_hvo = sandbox.WfiGlosses.GetCount(hvo)
                assert by_hvo == by_obj
                assert by_hvo >= 1
                assert gloss in list(sandbox.WfiGlosses.GetAll(hvo))
            finally:
                sandbox.WfiGlosses.Delete(gloss)
        finally:
            sandbox.Wordforms.Delete(wf)
