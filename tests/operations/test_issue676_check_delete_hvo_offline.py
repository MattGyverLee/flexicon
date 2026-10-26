#
#   test_issue676_check_delete_hvo_offline.py
#
#   Offline ratchet for issue #676 DeleteCheckType HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CHECK_OPS = REPO_ROOT / "flexicon" / "code" / "System" / "CheckOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue676_check_delete_hvo_live.py"
)


def _delete_check_type_block(text: str) -> str:
    start = text.index("def DeleteCheckType")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue676_delete_check_type_uses_hvo_membership():
    block = _delete_check_type_block(CHECK_OPS.read_text(encoding="utf-8"))
    assert "issue #676" in block
    assert "poss.Hvo == target_hvo" in block
    assert "sub.Hvo == target_hvo" in block
    assert "check_obj in check_list.PossibilitiesOS" not in block
    assert "check_obj in parent.SubPossibilitiesOS" not in block


def test_issue676_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #676"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "DeleteCheckType" in body
