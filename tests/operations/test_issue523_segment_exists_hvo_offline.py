#
#   test_issue523_segment_exists_hvo_offline.py
#
#   Offline ratchet for issue #523 SegmentOperations Exists HVO membership.
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
    / "test_issue523_segment_exists_hvo_live.py"
)


def _exists_block(text: str) -> str:
    start = text.index("def Exists")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue523_exists_uses_hvo_membership():
    block = _exists_block(SEGMENT_OPS.read_text(encoding="utf-8"))
    assert "issue #523" in block
    assert "seg.Hvo == target_hvo" in block
    assert " in segments_list" not in block
    assert "segment_obj in " not in block


def test_issue523_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #523"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Exists" in body
