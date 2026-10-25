#
#   test_issue746_phoneme_removecode_hvo_offline.py
#
#   Offline ratchet for issue #746 Phoneme CodesOS HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PHONEME_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "PhonemeOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue746_phoneme_removecode_hvo_live.py"
)


def _remove_code_block(text: str) -> str:
    start = text.index("def RemoveCode(self, phoneme_or_hvo, code_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue746_remove_code_uses_hvo_member_for_remove():
    block = _remove_code_block(PHONEME_OPS.read_text(encoding="utf-8"))
    assert "issue #746" in block
    assert "member_to_remove" in block
    assert "CodesOS.Remove(member_to_remove)" in block
    assert "code not in phoneme.CodesOS" not in block


def test_issue746_remove_code_scans_codesos_by_hvo():
    block = _remove_code_block(PHONEME_OPS.read_text(encoding="utf-8"))
    assert "int(slot.Hvo) == target_hvo" in block


def test_issue746_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #746"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemoveCode" in body
