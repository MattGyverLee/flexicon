#
#   test_issue716_reversal_sense_hvo_offline.py
#
#   Offline ratchet for issue #716 ReversalIndexEntry SensesRS HVO membership.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
REVERSAL_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Reversal" / "ReversalIndexEntryOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue716_reversal_sense_hvo_live.py"
)


def _method_block(text: str, method_name: str) -> str:
    start = text.index(f"def {method_name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue716_add_sense_uses_hvo_membership():
    source = REVERSAL_OPS.read_text(encoding="utf-8")
    block = _method_block(source, "AddSense")
    assert "issue #716" in block
    assert "linked.Hvo == target_hvo" in block
    assert "sense not in entry.SensesRS" not in block
    assert "sense in entry.SensesRS" not in block


def test_issue716_remove_sense_uses_hvo_membership():
    source = REVERSAL_OPS.read_text(encoding="utf-8")
    block = _method_block(source, "RemoveSense")
    assert "issue #716" in block
    assert "linked.Hvo == target_hvo" in block
    assert "sense in entry.SensesRS" not in block
    assert "Remove(sense)" not in block


def test_issue716_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #716"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "AddSense" in body or "RemoveSense" in body
