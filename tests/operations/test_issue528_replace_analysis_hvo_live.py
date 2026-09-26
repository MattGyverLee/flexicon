#
#   test_issue528_replace_analysis_hvo_live.py
#
#   Live verification for issue #528 ReplaceAnalysis AnalysesRS HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_528_"


class TestIssue528ReplaceAnalysisHvoLive:
    """ReplaceAnalysis must find the old token when passed as raw Object(hvo)."""

    @pytest.mark.live_phase("SegmentOperations", "modify")
    def test_replace_finds_old_token_via_raw_object_hvo(self, target_sandbox):
        sandbox = target_sandbox
        text = sandbox.Texts.Create(f"{TEST_PREFIX}replace")
        para = sandbox.Paragraphs.Create(text, f"{TEST_PREFIX}Hello")
        seg = list(sandbox.Segments.GetAll(para))[0]
        wf_old = sandbox.Wordforms.Create(f"{TEST_PREFIX}old")
        try:
            sandbox.Segments.AppendAnalysis(seg, wf_old)
            old_hvo = wf_old.Hvo
            raw_old = sandbox.Object(old_hvo)
            wf_new = sandbox.Wordforms.Create(f"{TEST_PREFIX}new")
            try:
                sandbox.Segments.ReplaceAnalysis(seg, raw_old, wf_new)
                remaining = {tok.Hvo for tok in sandbox.Segments.GetAnalyses(seg)}
                assert wf_new.Hvo in remaining
                assert old_hvo not in remaining
            finally:
                sandbox.Wordforms.Delete(wf_new)
        finally:
            sandbox.Wordforms.Delete(wf_old)
