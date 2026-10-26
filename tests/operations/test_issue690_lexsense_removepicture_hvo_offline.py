#
#   test_issue690_lexsense_removepicture_hvo_offline.py
#
#   Offline ratchet for issue #690 LexSense RemovePicture HVO membership lookup.
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
    / "test_issue690_lexsense_removepicture_hvo_live.py"
)


def _remove_picture_block(text: str) -> str:
    start = text.index("def RemovePicture(self, sense_or_hvo, picture, delete_file=False):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue690_remove_picture_uses_hvo_membership():
    block = _remove_picture_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #690" in block
    assert "linked.Hvo == target_hvo" in block
    assert "picture not in sense.PicturesOS" not in block


def test_issue690_remove_picture_removes_sequence_member():
    block = _remove_picture_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "linked_picture" in block
    assert "sense.PicturesOS.Remove(linked_picture)" in block


def test_issue690_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #690"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemovePicture" in body
