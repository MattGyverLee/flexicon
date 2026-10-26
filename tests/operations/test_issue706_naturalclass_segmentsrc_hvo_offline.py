#
#   test_issue706_naturalclass_segmentsrc_hvo_offline.py
#
#   Offline ratchet for issue #706 NaturalClass SegmentsRC HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NC_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "NaturalClassOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue706_naturalclass_segmentsrc_hvo_live.py"
)


def _add_phoneme_block(text: str) -> str:
    start = text.index("def AddPhoneme(self, nc_or_hvo, phoneme_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_phoneme_block(text: str) -> str:
    start = text.index("def RemovePhoneme(self, nc_or_hvo, phoneme_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue706_add_phoneme_uses_hvo_membership():
    block = _add_phoneme_block(NC_OPS.read_text(encoding="utf-8"))
    assert "issue #706" in block
    assert "int(seg.Hvo) == target_hvo" in block
    assert "phoneme not in nc.SegmentsRC" not in block


def test_issue706_remove_phoneme_uses_hvo_member_for_remove():
    block = _remove_phoneme_block(NC_OPS.read_text(encoding="utf-8"))
    assert "issue #706" in block
    assert "member_to_remove" in block
    assert "SegmentsRC.Remove(member_to_remove)" in block
    assert "phoneme not in nc.SegmentsRC" not in block


def test_issue706_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #706"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "AddPhoneme" in body
    assert "RemovePhoneme" in body
