#
#   test_issue776_baseops_sort_hvo_offline.py
#
#   Offline ratchet for issue #776 Sort / _ApplySequenceOrder HVO lookup.
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
    / "test_issue776_baseops_sort_hvo_live.py"
)


def _method_block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue776_sort_uses_hvo_identity():
    text = BASE_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "Sort")
    assert "issue #776" in block
    assert "_SameLcmObjectByHvo" in block
    assert "sequence[j] == items_with_indices" not in block


def test_issue776_apply_sequence_order_uses_hvo_identity():
    text = BASE_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "_ApplySequenceOrder")
    assert "issue #776" in block
    assert "_SameLcmObjectByHvo" in block
    assert "_HvoSetForObjects" in block
    assert "set(current) != set(desired_order)" not in block
    assert "sequence[j] == target_item" not in block


def test_issue776_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #776"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Sort" in body or "_ApplySequenceOrder" in body
