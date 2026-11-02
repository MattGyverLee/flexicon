#
#   test_issue686_pronunciation_movemedia_hvo_offline.py
#
#   Offline ratchet for issue #686 Pronunciation MoveMediaFile HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PRON_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "PronunciationOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue686_pronunciation_movemedia_hvo_live.py"
)


def _move_media_block(text: str) -> str:
    start = text.index(
        "def MoveMediaFile(self, media, from_pronunciation_or_hvo, to_pronunciation_or_hvo):"
    )
    next_def = text.find("\n    # --- CV Pattern", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _find_owned_block(text: str) -> str:
    start = text.index("def __FindOwnedMedia(self, pronunciation, media_or_hvo):")
    return text[start : text.index("    @OperationsMethod", start)]


def test_issue686_move_media_uses_hvo_membership():
    text = PRON_OPS.read_text(encoding="utf-8")
    block = _move_media_block(text)
    # Membership resolution lives in __FindOwnedMedia (issue #828) and is
    # still by HVO (issue #686); MoveMediaFile must delegate to it.
    assert "issue #686" in block
    assert "self.__FindOwnedMedia(from_pron, media)" in block
    helper = _find_owned_block(text)
    assert "f.Hvo == target_hvo" in helper
    assert "media not in from_pron.MediaFilesOS" not in block


def test_issue686_move_media_still_reparents_with_add_only():
    block = _move_media_block(PRON_OPS.read_text(encoding="utf-8"))
    assert block.count("to_pron.MediaFilesOS.Add(") == 1
    assert "to_pron.MediaFilesOS.Add(owned_media)" in block
    assert ".Remove(" not in block


def test_issue686_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #686"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "MoveMediaFile" in body
