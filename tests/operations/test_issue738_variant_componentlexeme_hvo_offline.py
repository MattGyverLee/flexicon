#
#   test_issue738_variant_componentlexeme_hvo_offline.py
#
#   Offline ratchet for issue #738 Variant ComponentLexemesRS HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
VARIANT_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "VariantOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue738_variant_componentlexeme_hvo_live.py"
)


def _add_block(text: str) -> str:
    start = text.index("def AddComponentLexeme(self, variant_or_hvo, entry_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_block(text: str) -> str:
    start = text.index("def RemoveComponentLexeme(self, variant_or_hvo, entry_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue738_add_component_lexeme_uses_hvo_membership():
    block = _add_block(VARIANT_OPS.read_text(encoding="utf-8"))
    assert "issue #738" in block
    assert "int(item.Hvo) == target_hvo" in block
    assert "entry in variant.ComponentLexemesRS" not in block


def test_issue738_remove_component_lexeme_uses_hvo_member_for_remove():
    block = _remove_block(VARIANT_OPS.read_text(encoding="utf-8"))
    assert "issue #738" in block
    assert "member_to_remove" in block
    assert "ComponentLexemesRS.Remove(member_to_remove)" in block
    assert "entry in variant.ComponentLexemesRS" not in block


def test_issue738_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #738"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "AddComponentLexeme" in body
    assert "RemoveComponentLexeme" in body
