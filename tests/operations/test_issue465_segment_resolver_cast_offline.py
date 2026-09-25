#
#   test_issue465_segment_resolver_cast_offline.py
#
#   Offline ratchet for issue #465 SegmentOperations HVO resolver casts.
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
    / "test_issue465_segment_resolver_cast_live.py"
)


def test_issue465_resolvers_use_cast_to_concrete():
    text = SEGMENT_OPS.read_text(encoding="utf-8")
    assert "cast_to_concrete" in text
    assert text.count("cast_to_concrete(self.project.Object") >= 2
    for helper in (
        "__GetSegmentObject",
        "__GetParagraphObject",
    ):
        assert f"def {helper}" in text
    assert "return self.project.Object(para_or_hvo)" not in text
    assert "return self.project.Object(segment_or_hvo)" not in text


def test_issue465_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #465"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "GetAnalyses" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
