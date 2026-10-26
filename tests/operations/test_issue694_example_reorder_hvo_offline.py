#
#   test_issue694_example_reorder_hvo_offline.py
#
#   Offline ratchet for issue #694 Example Reorder HVO membership partition.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXAMPLE_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "ExampleOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue694_example_reorder_hvo_live.py"
)


def _reorder_block(text: str) -> str:
    start = text.index("def Reorder(self, sense_or_hvo, example_list):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue694_reorder_partitions_by_hvo():
    block = _reorder_block(EXAMPLE_OPS.read_text(encoding="utf-8"))
    assert "issue #694" in block
    assert "example_by_hvo" in block
    assert "current_examples = set(sense.ExamplesOS)" not in block
    assert "new_examples = set(examples)" not in block


def test_issue694_reorder_builds_desired_order_from_sequence_members():
    block = _reorder_block(EXAMPLE_OPS.read_text(encoding="utf-8"))
    assert "desired_order = [example_by_hvo[hvo]" in block


def test_issue694_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #694"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Reorder" in body
