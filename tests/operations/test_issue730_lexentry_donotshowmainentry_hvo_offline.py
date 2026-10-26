#
#   test_issue730_lexentry_donotshowmainentry_hvo_offline.py
#
#   Offline ratchet for issue #730 LexEntry DoNotShowMainEntryInRC HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRY_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexEntryOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue730_lexentry_donotshowmainentry_hvo_live.py"
)


def _add_block(text: str) -> str:
    start = text.index("def AddDoNotShowMainEntryIn(self, entry_or_hvo, publication):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_block(text: str) -> str:
    start = text.index("def RemoveDoNotShowMainEntryIn(self, entry_or_hvo, publication):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue730_add_donotshowmainentry_uses_hvo_membership():
    block = _add_block(ENTRY_OPS.read_text(encoding="utf-8"))
    assert "issue #730" in block
    assert "pub.Hvo == target_hvo" in block
    assert "publication not in entry.DoNotShowMainEntryInRC" not in block
    assert "publication in entry.DoNotShowMainEntryInRC" not in block


def test_issue730_remove_donotshowmainentry_uses_hvo_membership():
    block = _remove_block(ENTRY_OPS.read_text(encoding="utf-8"))
    assert "issue #730" in block
    assert "linked.Hvo == target_hvo" in block
    assert "publication in entry.DoNotShowMainEntryInRC" not in block


def test_issue730_live_gate_module_exists():
    assert LIVE_GATE.is_file()
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemoveDoNotShowMainEntryIn" in body or "AddDoNotShowMainEntryIn" in body
