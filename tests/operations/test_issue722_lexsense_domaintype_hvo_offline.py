#
#   test_issue722_lexsense_domaintype_hvo_offline.py
#
#   Offline ratchet for issue #722 LexSense DomainTypesRC HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SENSE_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexSenseOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue722_lexsense_domaintype_hvo_live.py"
)


def _add_domain_type_block(text: str) -> str:
    start = text.index("def AddDomainType(self, sense_or_hvo, domain_type):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_domain_type_block(text: str) -> str:
    start = text.index("def RemoveDomainType(self, sense_or_hvo, domain_type):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue722_add_domain_type_uses_hvo_membership():
    block = _add_domain_type_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #722" in block
    assert "item.Hvo == target_hvo" in block
    assert "domain_type not in sense.DomainTypesRC" not in block
    assert "domain_type in sense.DomainTypesRC" not in block


def test_issue722_remove_domain_type_uses_hvo_membership():
    block = _remove_domain_type_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #722" in block
    assert "linked.Hvo == target_hvo" in block
    assert "domain_type in sense.DomainTypesRC" not in block


def test_issue722_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #722"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemoveDomainType" in body or "AddDomainType" in body
