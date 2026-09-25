#
#   test_issue521_segment_get_owning_paragraph_offline.py
#
#   Offline ratchet for issue #521 GetOwningParagraph and MergeSegments owner gate.
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
    / "test_issue521_segment_get_owning_paragraph_live.py"
)


def _get_owning_paragraph_block(text: str) -> str:
    start = text.index("def GetOwningParagraph")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _merge_segments_block(text: str) -> str:
    start = text.index("def MergeSegments")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue521_get_owning_paragraph_uses_typed_owner():
    source = SEGMENT_OPS.read_text(encoding="utf-8")
    block = _get_owning_paragraph_block(source)
    assert "_GetTypedOwner(segment_obj)" in block
    assert "issue #521" in block
    assert "segment_obj.Paragraph" not in block


def test_issue521_merge_segments_compares_typed_owner_hvo():
    block = _merge_segments_block(SEGMENT_OPS.read_text(encoding="utf-8"))
    assert "para1.Hvo != para2.Hvo" in block
    assert "seg1.Owner != seg2.Owner" not in block


def test_issue521_write_paths_use_get_owning_paragraph():
    source = SEGMENT_OPS.read_text(encoding="utf-8")
    assert source.count("GetOwningParagraph(segment_obj)") >= 1
    assert source.count("GetOwningParagraph(seg)") >= 1
    assert "segment_obj.Paragraph" not in source
    assert "seg.Paragraph" not in source


def test_issue521_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #521"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetOwningParagraph" in body
