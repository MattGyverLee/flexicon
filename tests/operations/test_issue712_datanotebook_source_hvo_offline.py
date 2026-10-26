#
#   test_issue712_datanotebook_source_hvo_offline.py
#
#   Offline ratchet for issue #712 DataNotebook source HVO membership lookup.
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
    / "test_issue712_datanotebook_source_hvo_live.py"
)


def _add_source_block(text: str) -> str:
    start = text.index("def AddSource(self, record_or_hvo, source):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_source_block(text: str) -> str:
    start = text.index("def RemoveSource(self, record_or_hvo, source):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue712_add_source_uses_hvo_membership():
    block = _add_source_block(DATA_OPS.read_text(encoding="utf-8"))
    assert "issue #712" in block
    assert "src.Hvo == target_hvo" in block
    assert "source not in record.SourcesRC" not in block


def test_issue712_remove_source_uses_hvo_membership():
    block = _remove_source_block(DATA_OPS.read_text(encoding="utf-8"))
    assert "issue #712" in block
    assert "linked.Hvo == target_hvo" in block
    assert "source in record.SourcesRC" not in block


def test_issue712_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #712"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "AddSource" in body or "RemoveSource" in body
