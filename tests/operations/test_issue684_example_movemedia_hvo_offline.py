#
#   test_issue684_example_movemedia_hvo_offline.py
#
#   Offline ratchet for issue #684 Example MoveMediaFile HVO membership lookup.
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
    / "test_issue684_example_movemedia_hvo_live.py"
)


def _move_media_block(text: str) -> str:
    start = text.index("def MoveMediaFile(self, media, from_example_or_hvo, to_example_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue684_move_media_uses_hvo_membership():
    block = _move_media_block(EXAMPLE_OPS.read_text(encoding="utf-8"))
    assert "issue #684" in block
    assert "f.Hvo == target_hvo" in block
    assert "media not in from_example.MediaFilesOS" not in block


def test_issue684_move_media_still_reparents_with_add_only():
    block = _move_media_block(EXAMPLE_OPS.read_text(encoding="utf-8"))
    assert "to_example.MediaFilesOS.Add(media)" in block
    assert ".Remove(media)" not in block


def test_issue684_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #684"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "MoveMediaFile" in body
