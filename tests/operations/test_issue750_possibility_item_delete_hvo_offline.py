#
#   test_issue750_possibility_item_delete_hvo_offline.py
#
#   Offline ratchet for issue #750 PossibilityItemOperations Delete HVO membership.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
POSS_ITEM_BASE = (
    REPO_ROOT / "flexicon" / "code" / "Lists" / "possibility_item_base.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue750_possibility_item_delete_hvo_live.py"
)


def _delete_block(text: str) -> str:
    start = text.index("def Delete(self, item_or_hvo)")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue750_delete_uses_hvo_membership():
    block = _delete_block(POSS_ITEM_BASE.read_text(encoding="utf-8"))
    assert "issue #750" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "item in list_obj.PossibilitiesOS" not in block


def test_issue750_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #750"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
