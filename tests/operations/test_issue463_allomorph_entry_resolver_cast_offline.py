#
#   test_issue463_allomorph_entry_resolver_cast_offline.py
#
#   Offline ratchet for issue #463 AllomorphOperations __GetEntryObject cast.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ALLOMORPH_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "AllomorphOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue463_allomorph_entry_resolver_cast_live.py"
)


def test_issue463_get_entry_object_uses_cast_to_concrete():
    text = ALLOMORPH_OPS.read_text(encoding="utf-8")
    assert "cast_to_concrete" in text
    assert "def __GetEntryObject" in text
    assert "return self.project.Object(entry_or_hvo)" not in text
    helper_start = text.index("def __GetEntryObject")
    helper_chunk = text[helper_start : helper_start + 600]
    assert "cast_to_concrete(entry_or_hvo)" in helper_chunk


def test_issue463_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #463"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "Create" in text
    assert "isinstance(entry_hvo, int)" in text
    assert "requires_live_project" in text
