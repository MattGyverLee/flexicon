#
#   test_issue760_semanticdomain_delete_hvo_offline.py
#
#   Offline ratchet for issue #760 SemanticDomainOperations Delete HVO membership.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SEM_DOMAIN_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "SemanticDomainOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue760_semanticdomain_delete_hvo_live.py"
)


def _delete_block(text: str) -> str:
    start = text.index("def Delete(self, domain_or_hvo)")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue760_delete_uses_hvo_membership():
    block = _delete_block(SEM_DOMAIN_OPS.read_text(encoding="utf-8"))
    assert "issue #760" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "SubPossibilitiesOS.Remove(domain)" not in block
    assert "PossibilitiesOS.Remove(domain)" not in block


def test_issue760_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #760"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
