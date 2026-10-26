#
#   test_issue708_datanotebook_researcher_hvo_offline.py
#
#   Offline ratchet for issue #708 DataNotebook researcher HVO membership lookup.
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
    / "test_issue708_datanotebook_researcher_hvo_live.py"
)


def _add_researcher_block(text: str) -> str:
    start = text.index("def AddResearcher(self, record_or_hvo, person):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_researcher_block(text: str) -> str:
    start = text.index("def RemoveResearcher(self, record_or_hvo, person):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue708_add_researcher_uses_hvo_membership():
    block = _add_researcher_block(DATA_OPS.read_text(encoding="utf-8"))
    assert "issue #708" in block
    assert "p.Hvo == target_hvo" in block
    assert "person not in record.ResearchersRC" not in block


def test_issue708_remove_researcher_uses_hvo_membership():
    block = _remove_researcher_block(DATA_OPS.read_text(encoding="utf-8"))
    assert "issue #708" in block
    assert "linked.Hvo == target_hvo" in block
    assert "person in record.ResearchersRC" not in block


def test_issue708_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #708"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "AddResearcher" in body or "RemoveResearcher" in body
