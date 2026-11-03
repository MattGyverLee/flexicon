#
#   test_issue864_phon_handle_children_closed_offline.py
#
#   Offline ratchet for issue #864 _handle_entry_children IFsClosedFeature guard.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PHON_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "PhonFeatureOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue864_phon_handle_children_closed_live.py"
)


def _handle_entry_children_block(text: str) -> str:
    start = text.index("def _handle_entry_children(")
    next_def = text.find("\n    def _CreateValueFromEntry(", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue864_handle_entry_children_cast_guard_present():
    block = _handle_entry_children_block(PHON_OPS.read_text(encoding="utf-8"))
    assert "issue #864" in block
    assert "except (AttributeError, System.InvalidCastException):" in block
    assert "_handle_entry_children requires an IFsClosedFeature parent" in block
    guard_pos = block.index("issue #864")
    values_pos = block.index("existing_value_guids = {")
    assert guard_pos < values_pos


def test_issue864_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #864"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "_handle_entry_children" in body
