#
#   test_issue736_overlay_possitems_hvo_offline.py
#
#   Offline ratchet for issue #736 Overlay PossItemsRC HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OVERLAY_OPS = REPO_ROOT / "flexicon" / "code" / "Lists" / "OverlayOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue736_overlay_possitems_hvo_live.py"
)


def _add_element_block(text: str) -> str:
    start = text.index("def AddElement(self, overlay_or_hvo, element):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_element_block(text: str) -> str:
    start = text.index("def RemoveElement(self, overlay_or_hvo, element):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue736_add_element_uses_hvo_membership():
    block = _add_element_block(OVERLAY_OPS.read_text(encoding="utf-8"))
    assert "issue #736" in block
    assert "int(item.Hvo) == target_hvo" in block
    assert "element not in overlay.PossItemsRC" not in block


def test_issue736_remove_element_uses_hvo_member_for_remove():
    block = _remove_element_block(OVERLAY_OPS.read_text(encoding="utf-8"))
    assert "issue #736" in block
    assert "member_to_remove" in block
    assert "PossItemsRC.Remove(member_to_remove)" in block
    assert "element in overlay.PossItemsRC" not in block


def test_issue736_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #736"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "AddElement" in body
    assert "RemoveElement" in body
