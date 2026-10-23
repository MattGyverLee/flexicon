#
#   test_issue670_split_segment_hvo_offline.py
#
#   Offline ratchet for issue #670 SplitSegment SegmentsOS HVO index.
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
    / "test_issue670_split_segment_hvo_live.py"
)


def _split_segment_block(text: str) -> str:
    start = text.index("def SplitSegment")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue670_split_segment_uses_hvo_index():
    block = _split_segment_block(SEGMENT_OPS.read_text(encoding="utf-8"))
    assert "issue #670" in block
    assert "member.Hvo == seg_hvo" in block
    assert "IndexOf(seg)" not in block


def test_issue670_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #670"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "SplitSegment" in body
