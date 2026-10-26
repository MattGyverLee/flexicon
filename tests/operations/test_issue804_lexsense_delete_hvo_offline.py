#
#   test_issue804_lexsense_delete_hvo_offline.py
#
#   Offline ratchet for issue #804 LexSenseOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LEX_SENSE_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexSenseOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue804_lexsense_delete_hvo_live.py"
)


def _delete_block(text: str) -> str:
    start = text.index("def Delete(self, sense_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue804_delete_uses_hvo_membership():
    block = _delete_block(LEX_SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #804" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "SensesOS.Remove(sense)" not in block


def test_issue804_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #804"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
