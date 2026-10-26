#
#   test_issue752_dependent_clause_hvo_offline.py
#
#   Offline ratchet for issue #752 DependentClausesRS HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OPS = REPO_ROOT / "flexicon" / "code" / "Discourse" / "ConstChartClauseMarkerOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue752_dependent_clause_hvo_live.py"
)


def _add_dependent_clause_block(text: str) -> str:
    start = text.index("def AddDependentClause(self, marker_or_hvo, clause_marker):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue752_add_dependent_clause_uses_hvo_membership():
    block = _add_dependent_clause_block(OPS.read_text(encoding="utf-8"))
    assert "issue #752" in block
    assert "dep.Hvo == target_hvo" in block
    assert "clause_marker not in marker.DependentClausesRS" not in block
    assert "clause_marker in marker.DependentClausesRS" not in block


def test_issue752_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #752"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "AddDependentClause" in body
