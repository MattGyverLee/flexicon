#
#   test_issue528_replace_analysis_hvo_offline.py
#
#   Offline ratchet for issue #528 ReplaceAnalysis AnalysesRS HVO membership.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SEGMENT_OPS = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "SegmentOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue528_replace_analysis_hvo_live.py"
)


def _replace_analysis_block(text: str) -> str:
    start = text.index("def ReplaceAnalysis")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue528_replace_analysis_uses_hvo_membership():
    block = _replace_analysis_block(SEGMENT_OPS.read_text(encoding="utf-8"))
    assert "issue #528" in block
    assert "token.Hvo == old_hvo" in block
    assert "analyses.index(old_obj)" not in block
    assert "old_obj not in analyses" not in block


def test_issue528_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #528"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "ReplaceAnalysis" in body
