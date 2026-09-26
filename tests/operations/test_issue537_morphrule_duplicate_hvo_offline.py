#
#   test_issue537_morphrule_duplicate_hvo_offline.py
#
#   Offline ratchet for issue #537 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MORPH_RULE_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "MorphRuleOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue537_morphrule_duplicate_hvo_live.py"
)


def _method_block(text: str, method_name: str) -> str:
    needle = f"def {method_name}"
    start = text.index(needle)
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue537_duplicate_compound_rule_uses_hvo_index():
    text = MORPH_RULE_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "__DuplicateCompoundRule")
    assert "issue #537" in block
    assert "rule.Hvo == target_hvo" in block
    assert "CompoundRulesOS.IndexOf(source)" not in block


def test_issue537_duplicate_affix_template_uses_hvo_index():
    text = MORPH_RULE_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "__DuplicateAffixTemplate")
    assert "issue #537" in block
    assert "tmpl.Hvo == target_hvo" in block
    assert "AffixTemplatesOS.IndexOf(source)" not in block


def test_issue537_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #537"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Duplicate" in body
