#
#   test_issue656_semanticdomain_duplicate_hvo_offline.py
#
#   Offline ratchet for issue #656 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SEMANTIC_DOMAIN_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Lexicon" / "SemanticDomainOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue656_semanticdomain_duplicate_hvo_live.py"
)


def _duplicate_block(text: str) -> str:
    start = text.index("def Duplicate")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue656_duplicate_insert_after_uses_hvo_index():
    block = _duplicate_block(SEMANTIC_DOMAIN_OPS.read_text(encoding="utf-8"))
    assert "issue #656" in block
    assert "domain.Hvo == target_hvo" in block or "subdomain.Hvo == target_hvo" in block
    assert "SubPossibilitiesOS.IndexOf(source)" not in block
    assert "PossibilitiesOS.IndexOf(source)" not in block


def test_issue656_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #656"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Duplicate" in body
