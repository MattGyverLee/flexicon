#
#   test_issue754_possibility_list_delete_hvo_offline.py
#
#   Offline ratchet for issue #754 PossibilityListOperations DeleteItem HVO lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OPS = REPO_ROOT / "flexicon" / "code" / "Lists" / "PossibilityListOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue754_possibility_list_delete_hvo_live.py"
)


def _delete_item_block(text: str) -> str:
    start = text.index("def DeleteItem(self, item_or_hvo)")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue754_delete_item_uses_hvo_membership():
    block = _delete_item_block(OPS.read_text(encoding="utf-8"))
    assert "issue #754" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "SubPossibilitiesOS.Remove(item)" not in block
    assert "PossibilitiesOS.Remove(item)" not in block


def test_issue754_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #754"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "DeleteItem" in body
