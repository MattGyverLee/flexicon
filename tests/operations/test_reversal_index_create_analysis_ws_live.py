#
#   test_reversal_index_create_analysis_ws_live.py
#
#   Live write-path verification for issue #605: ReversalIndexOperations
#   .Create rejects a non-analysis writing system before any mutation.
#   Uses target_sandbox only (tempdir copy of the Target .fwbackup).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def _index_tags(project):
    return sorted(str(i.WritingSystem) for i in project.ReversalIndexes.GetAll())


def _free_ws(project, vernacular):
    ops = project.WritingSystems
    source = ops.GetVernacular() if vernacular else ops.GetAnalysis()
    analysis_tags = {ops.GetLanguageTag(w) for w in ops.GetAnalysis()}
    for ws in source:
        tag = ops.GetLanguageTag(ws)
        if vernacular and tag in analysis_tags:
            continue
        if project.ReversalIndexes.FindByWritingSystem(tag) is None:
            return ws, tag
    return None, None


class TestReversalCreateAnalysisWS:
    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_vernacular_ws_rejected_and_nothing_created(self, target_sandbox):
        ws, tag = _free_ws(target_sandbox, vernacular=True)
        assert ws is not None, "no vernacular-only WS in Target"
        before = _index_tags(target_sandbox)

        for arg in (tag, int(ws.Handle)):
            with pytest.raises(FP_ParameterError):
                target_sandbox.ReversalIndexes.Create(f"{TEST_PREFIX}vern", arg)

        after = _index_tags(target_sandbox)
        assert after == before, f"index list changed: {before} -> {after}"

    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_analysis_ws_still_creates(self, target_sandbox):
        """Analysis WS creates fine. Target already has an 'en' index, so
        delete it first (sandbox copy only) to free the analysis WS."""
        rev = target_sandbox.ReversalIndexes
        ws, tag = _free_ws(target_sandbox, vernacular=False)
        if ws is None:
            ops = target_sandbox.WritingSystems
            tag = ops.GetLanguageTag(next(iter(ops.GetAnalysis())))
            existing = rev.FindByWritingSystem(tag)
            assert existing is not None
            rev.Delete(existing)
            assert tag not in _index_tags(target_sandbox)
        before = len(_index_tags(target_sandbox))
        created = rev.Create(f"{TEST_PREFIX}anal", tag)
        assert created is not None
        after = _index_tags(target_sandbox)
        assert len(after) == before + 1
        assert tag in after
