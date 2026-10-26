#
#   test_issue710_datanotebook_location_hvo_offline.py
#
#   Offline ratchet for issue #710 DataNotebook location HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DATA_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "DataNotebookOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue710_datanotebook_location_hvo_live.py"
)


def _add_location_block(text: str) -> str:
    start = text.index("def AddLocation(self, record_or_hvo, location):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_location_block(text: str) -> str:
    start = text.index("def RemoveLocation(self, record_or_hvo, location):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue710_add_location_uses_hvo_membership():
    block = _add_location_block(DATA_OPS.read_text(encoding="utf-8"))
    assert "issue #710" in block
    assert "loc.Hvo == target_hvo" in block
    assert "location not in record.LocationsRC" not in block


def test_issue710_remove_location_uses_hvo_membership():
    block = _remove_location_block(DATA_OPS.read_text(encoding="utf-8"))
    assert "issue #710" in block
    assert "linked.Hvo == target_hvo" in block
    assert "location in record.LocationsRC" not in block


def test_issue710_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #710"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "AddLocation" in body or "RemoveLocation" in body
