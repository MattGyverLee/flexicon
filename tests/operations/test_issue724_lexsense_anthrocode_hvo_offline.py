#
#   test_issue724_lexsense_anthrocode_hvo_offline.py
#
#   Offline ratchet for issue #724 LexSense AnthroCodesRC HVO membership lookup.
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
    / "test_issue724_lexsense_anthrocode_hvo_live.py"
)


def _add_anthro_code_block(text: str) -> str:
    start = text.index("def AddAnthroCode(self, sense_or_hvo, anthro_code):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_anthro_code_block(text: str) -> str:
    start = text.index("def RemoveAnthroCode(self, sense_or_hvo, anthro_code):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue724_add_anthro_code_uses_hvo_membership():
    block = _add_anthro_code_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #724" in block
    assert "code.Hvo == target_hvo" in block
    assert "anthro_code not in sense.AnthroCodesRC" not in block
    assert "anthro_code in sense.AnthroCodesRC" not in block


def test_issue724_remove_anthro_code_uses_hvo_membership():
    block = _remove_anthro_code_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #724" in block
    assert "linked.Hvo == target_hvo" in block
    assert "anthro_code in sense.AnthroCodesRC" not in block


def test_issue724_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #724"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemoveAnthroCode" in body or "AddAnthroCode" in body
