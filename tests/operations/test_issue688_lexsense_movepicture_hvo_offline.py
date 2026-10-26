#
#   test_issue688_lexsense_movepicture_hvo_offline.py
#
#   Offline ratchet for issue #688 LexSense MovePicture HVO membership lookup.
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
    / "test_issue688_lexsense_movepicture_hvo_live.py"
)


def _move_picture_block(text: str) -> str:
    start = text.index("def MovePicture(self, picture, from_sense_or_hvo, to_sense_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue688_move_picture_uses_hvo_membership():
    block = _move_picture_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #688" in block
    assert "p.Hvo == target_hvo" in block
    assert "picture not in from_sense.PicturesOS" not in block


def test_issue688_move_picture_still_reparents_with_add_only():
    block = _move_picture_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "to_sense.PicturesOS.Add(picture)" in block
    assert ".Remove(picture)" not in block


def test_issue688_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #688"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "MovePicture" in body
