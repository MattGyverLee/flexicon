#
#   test_issue550_lexsense_duplicate_hvo_offline.py
#
#   Offline ratchet for issue #550 Duplicate insert_after HVO index lookup.
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
    / "test_issue550_lexsense_duplicate_hvo_live.py"
)


def _duplicate_block(text: str) -> str:
    start = text.index("def Duplicate")
    next_def = text.find("\n    def _deep_copy_sense_to", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue550_duplicate_insert_after_uses_hvo_index():
    block = _duplicate_block(LEX_SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #550" in block
    assert "sense.Hvo == target_hvo" in block
    assert "SensesOS.IndexOf(source)" not in block


def test_issue550_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #550"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Duplicate" in body
