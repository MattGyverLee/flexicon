#
#   test_issue874_morph_adjacency_sync_offline.py
#
#   Offline ratchet for issue #874 Adjacency in GetSyncableProperties.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MORPH_OPS = (
    REPO_ROOT
    / "flexicon"
    / "code"
    / "Grammar"
    / "MorphRuleOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue874_morph_adjacency_sync_live.py"
)


def _get_sync_block(text: str) -> str:
    start = text.index("def GetSyncableProperties(self, item):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue874_adjacency_emitted_in_get_syncable_properties():
    block = _get_sync_block(MORPH_OPS.read_text(encoding="utf-8"))
    assert "issue #874" in block
    assert 'hasattr(rule, "Adjacency")' in block
    assert "int(rule.Adjacency)" in block
    assert 'props["Adjacency"]' in block


def test_issue874_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #874"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Adjacency" in body
