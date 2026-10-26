#
#   test_issue726_lexsense_donotpublish_hvo_offline.py
#
#   Offline ratchet for issue #726 LexSense DoNotPublishInRC HVO membership lookup.
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
    / "test_issue726_lexsense_donotpublish_hvo_live.py"
)


def _add_block(text: str) -> str:
    start = text.index("def AddDoNotPublishIn(self, sense_or_hvo, publication):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_block(text: str) -> str:
    start = text.index("def RemoveDoNotPublishIn(self, sense_or_hvo, publication):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue726_add_donotpublish_uses_hvo_membership():
    block = _add_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #726" in block
    assert "pub.Hvo == target_hvo" in block
    assert "publication not in sense.DoNotPublishInRC" not in block
    assert "publication in sense.DoNotPublishInRC" not in block


def test_issue726_remove_donotpublish_uses_hvo_membership():
    block = _remove_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #726" in block
    assert "linked.Hvo == target_hvo" in block
    assert "publication in sense.DoNotPublishInRC" not in block


def test_issue726_live_gate_module_exists():
    assert LIVE_GATE.is_file()
