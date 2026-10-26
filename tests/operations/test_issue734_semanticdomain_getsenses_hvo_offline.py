#
#   test_issue734_semanticdomain_getsenses_hvo_offline.py
#
#   Offline ratchet for issue #734 GetSensesInDomain HVO membership.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SEM_DOM_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Lexicon" / "SemanticDomainOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue734_semanticdomain_getsenses_hvo_live.py"
)


def _getsenses_block(text: str) -> str:
    start = text.index("def GetSensesInDomain")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue734_getsenses_uses_hvo_membership():
    block = _getsenses_block(SEM_DOM_OPS.read_text(encoding="utf-8"))
    assert "issue #734" in block
    assert "d.Hvo == domain_hvo" in block
    assert "domain in sense.SemanticDomainsRC" not in block


def test_issue734_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #734"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetSensesInDomain" in body
