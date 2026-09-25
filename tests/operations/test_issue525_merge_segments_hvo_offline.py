#
#   test_issue525_merge_segments_hvo_offline.py
#
#   Offline ratchet for issue #525 MergeSegments SegmentsOS HVO index/remove.
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
    / "test_issue525_merge_segments_hvo_live.py"
)


def _merge_segments_block(text: str) -> str:
    start = text.index("def MergeSegments")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue525_merge_segments_uses_hvo_index():
    block = _merge_segments_block(SEGMENT_OPS.read_text(encoding="utf-8"))
    assert "issue #525" in block
    assert "seg.Hvo == seg1_hvo" in block or "seg.Hvo == seg2_hvo" in block
    assert ".index(seg1)" not in block
    assert ".index(seg2)" not in block


def test_issue525_merge_segments_remove_by_hvo():
    block = _merge_segments_block(SEGMENT_OPS.read_text(encoding="utf-8"))
    assert "seg.Hvo == seg2.Hvo" in block
    assert "seg2 in list(para.SegmentsOS)" not in block


def test_issue525_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #525"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "MergeSegments" in body
