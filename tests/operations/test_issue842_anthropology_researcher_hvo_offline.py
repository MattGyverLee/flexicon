#
#   test_issue842_anthropology_researcher_hvo_offline.py
#
#   Offline ratchet for issue #842 Anthropology researcher HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ANTHRO_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "AnthropologyOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue842_anthropology_researcher_hvo_live.py"
)


def _add_researcher_block(text: str) -> str:
    start = text.index("def AddResearcher(self, item_or_hvo, person):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_researcher_block(text: str) -> str:
    start = text.index("def RemoveResearcher(self, item_or_hvo, person):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue842_add_researcher_uses_hvo_membership():
    block = _add_researcher_block(ANTHRO_OPS.read_text(encoding="utf-8"))
    assert "issue #842" in block
    assert "p.Hvo == target_hvo" in block
    assert "ResearchersRC.Contains" not in block


def test_issue842_remove_researcher_uses_hvo_membership():
    block = _remove_researcher_block(ANTHRO_OPS.read_text(encoding="utf-8"))
    assert "issue #842" in block
    assert "linked.Hvo == target_hvo" in block
    assert "ResearchersRC.Contains" not in block
    assert "ResearchersRC.Remove(person_obj)" not in block


def test_issue842_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #842"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemoveResearcher" in body
