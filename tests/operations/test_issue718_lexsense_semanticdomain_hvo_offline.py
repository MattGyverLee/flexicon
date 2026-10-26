#
#   test_issue718_lexsense_semanticdomain_hvo_offline.py
#
#   Offline ratchet for issue #718 LexSense SemanticDomainsRC HVO membership lookup.
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
    / "test_issue718_lexsense_semanticdomain_hvo_live.py"
)


def _add_semantic_domain_block(text: str) -> str:
    start = text.index("def AddSemanticDomain(self, sense_or_hvo, domain_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_semantic_domain_block(text: str) -> str:
    start = text.index("def RemoveSemanticDomain(self, sense_or_hvo, domain_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue718_add_semantic_domain_uses_hvo_membership():
    block = _add_semantic_domain_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #718" in block
    assert "d.Hvo == target_hvo" in block
    assert "domain not in sense.SemanticDomainsRC" not in block
    assert "domain in sense.SemanticDomainsRC" not in block


def test_issue718_remove_semantic_domain_uses_hvo_membership():
    block = _remove_semantic_domain_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #718" in block
    assert "linked.Hvo == target_hvo" in block
    assert "domain in sense.SemanticDomainsRC" not in block


def test_issue718_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #718"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemoveSemanticDomain" in body or "AddSemanticDomain" in body
