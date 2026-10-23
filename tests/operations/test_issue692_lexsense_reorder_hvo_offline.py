#
#   test_issue692_lexsense_reorder_hvo_offline.py
#
#   Offline ratchet for issue #692 LexSense Reorder HVO membership partition.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SENSE_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexSenseOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue692_lexsense_reorder_hvo_live.py"
)


def _reorder_block(text: str) -> str:
    start = text.index("def Reorder(self, entry_or_hvo, sense_list):")
    next_def = text.find("\n    # --- Lookup ---", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue692_reorder_partitions_by_hvo():
    block = _reorder_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #692" in block
    assert "sense_by_hvo" in block
    assert "ordered_set = set(resolved_senses)" not in block
    assert "s not in ordered_set" not in block


def test_issue692_reorder_builds_desired_order_from_sequence_members():
    block = _reorder_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "desired_order = [" in block
    assert "sense_by_hvo[hvo]" in block


def test_issue692_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #692"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Reorder" in body
