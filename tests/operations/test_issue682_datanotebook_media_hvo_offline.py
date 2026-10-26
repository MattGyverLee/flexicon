#
#   test_issue682_datanotebook_media_hvo_offline.py
#
#   Offline ratchet for issue #682 DataNotebook media HVO membership lookup.
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
    / "test_issue682_datanotebook_media_hvo_live.py"
)


def _add_media_block(text: str) -> str:
    start = text.index("def AddMediaFile(self, record_or_hvo, media_file):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_media_block(text: str) -> str:
    start = text.index("def RemoveMediaFile(self, record_or_hvo, media_file):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue682_add_media_uses_hvo_membership():
    block = _add_media_block(DATA_OPS.read_text(encoding="utf-8"))
    assert "issue #682" in block
    assert "f.Hvo == target_hvo" in block
    assert "media_file not in record.MediaFilesOS" not in block


def test_issue682_remove_media_uses_hvo_membership():
    block = _remove_media_block(DATA_OPS.read_text(encoding="utf-8"))
    assert "issue #682" in block
    assert "linked.Hvo == target_hvo" in block
    assert "media_file in record.MediaFilesOS" not in block


def test_issue682_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #682"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "AddMediaFile" in body or "RemoveMediaFile" in body
