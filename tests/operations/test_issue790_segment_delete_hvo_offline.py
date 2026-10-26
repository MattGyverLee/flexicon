#
#   test_issue790_segment_delete_hvo_offline.py
#
#   Offline ratchet for issue #790 SegmentOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SEG_OPS = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "SegmentOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue790_segment_delete_hvo_live.py"
)


def _delete_block(text: str) -> str:
    start = text.index("def Delete(self, segment_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue790_delete_uses_hvo_membership():
    block = _delete_block(SEG_OPS.read_text(encoding="utf-8"))
    assert "issue #790" in block
    assert "int(seg.Hvo) == target_hvo" in block
    assert "SegmentsOS.Remove(segment_obj)" not in block


def test_issue790_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #790"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
