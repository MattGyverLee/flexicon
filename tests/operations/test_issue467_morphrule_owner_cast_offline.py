#
#   test_issue467_morphrule_owner_cast_offline.py
#
#   Offline ratchet for issue #467 MorphRuleOperations affix-template
#   Delete / Duplicate owner resolution.
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
    / "test_issue467_morphrule_owner_cast_live.py"
)


def test_issue467_delete_routes_owner_through_get_typed_owner():
    text = MORPH_RULE_OPS.read_text(encoding="utf-8")
    delete_start = text.index("def Delete(")
    delete_block = text[delete_start : text.index("\n    @OperationsMethod", delete_start)]
    assert "MoInflAffixTemplate" in delete_block
    assert "_GetTypedOwner(rule)" in delete_block
    assert "_GetObject(rule.Owner.Hvo)" not in delete_block


def test_issue467_duplicate_affix_template_routes_owner_through_get_typed_owner():
    text = MORPH_RULE_OPS.read_text(encoding="utf-8")
    dup_start = text.index("def __DuplicateAffixTemplate(")
    dup_block = text[dup_start : text.index("\n    # ==========", dup_start)]
    assert "_GetTypedOwner(source)" in dup_block
    assert "_GetObject(source.Owner.Hvo)" not in dup_block


def test_issue467_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #467"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "AffixTemplatesOS" in text
    assert "requires_live_project" in text
