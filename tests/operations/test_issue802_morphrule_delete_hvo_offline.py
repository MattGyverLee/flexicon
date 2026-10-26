#
#   test_issue802_morphrule_delete_hvo_offline.py
#
#   Offline ratchet for issue #802 MorphRuleOperations Delete HVO lookup.
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
    / "test_issue802_morphrule_delete_hvo_live.py"
)


def _block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue802_delete_uses_hvo_membership():
    text = MORPH_RULE_OPS.read_text(encoding="utf-8")
    block = _block(text, "Delete")
    assert "issue #802" in block
    assert "__RemoveMemberByHvo" in block
    assert "CompoundRulesOS.Remove(rule)" not in block
    assert "AffixTemplatesOS.Remove(rule)" not in block
    assert "AdhocCoProhibitionsOC.Remove(rule)" not in block


def test_issue802_remove_helper_uses_hvo():
    text = MORPH_RULE_OPS.read_text(encoding="utf-8")
    block = _block(text, "__RemoveMemberByHvo")
    assert "issue #802" in block
    assert "int(slot.Hvo) == target_hvo" in block


def test_issue802_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #802"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
