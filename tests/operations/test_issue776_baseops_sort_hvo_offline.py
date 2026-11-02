#
#   test_issue776_baseops_sort_hvo_offline.py
#
#   Offline ratchet for issue #776 (Sort / _ApplySequenceOrder HVO compare).
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BASE_OPS = REPO_ROOT / "flexicon" / "code" / "BaseOperations.py"
LIVE_GATE = REPO_ROOT / "tests" / "operations" / "test_issue776_baseops_sort_hvo_live.py"


def _block(name):
    text = BASE_OPS.read_text(encoding="utf-8")
    start = text.index(f"def {name}")
    end = text.find("\n    def ", start + 1)
    return text[start:end] if end != -1 else text[start:]


def test_issue776_sort_locates_by_hvo():
    b = _block("Sort")
    assert "_SameLcmObjectByHvo" in b
    assert "sequence[j] ==" not in b


def test_issue776_apply_sequence_order_compares_by_hvo():
    b = _block("_ApplySequenceOrder")
    assert "_SameLcmObjectByHvo" in b
    assert "_LcmObjectHvo" in b
    assert "set(current)" not in b
    assert "sequence[j] ==" not in b


def test_issue776_live_gate_module_exists():
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Sort" in body and "_ApplySequenceOrder" in body
