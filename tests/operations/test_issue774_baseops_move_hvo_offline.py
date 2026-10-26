#
#   test_issue774_baseops_move_hvo_offline.py
#
#   Offline ratchet for issue #774 BaseOperations move helper HVO lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BASE_OPS = REPO_ROOT / "flexicon" / "code" / "BaseOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue774_baseops_move_hvo_live.py"
)


def _method_block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue774_move_up_uses_hvo_index():
    text = BASE_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "MoveUp")
    assert "issue #774" in block
    assert "_IndexInOwningSequenceByHvo" in block
    assert "sequence[i] == item" not in block


def test_issue774_move_down_uses_hvo_index():
    text = BASE_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "MoveDown")
    assert "_IndexInOwningSequenceByHvo" in block
    assert "sequence[i] == item" not in block


def test_issue774_move_to_index_uses_hvo_index():
    text = BASE_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "MoveToIndex")
    assert "_IndexInOwningSequenceByHvo" in block
    assert "sequence[i] == item" not in block


def test_issue774_find_common_sequence_uses_hvo():
    text = BASE_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "_FindCommonSequence")
    assert "_SameLcmObjectByHvo" in block
    assert "item == item1" not in block


def test_issue774_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #774"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "MoveDown" in body
