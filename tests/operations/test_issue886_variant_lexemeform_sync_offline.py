#
#   test_issue886_variant_lexemeform_sync_offline.py
#
#   Offline ratchet for issue #886 owning-entry LexemeForm sync fields.
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
    / "test_issue886_variant_lexemeform_sync_live.py"
)


def _method_block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue886_get_syncable_properties_emits_lexeme_form():
    text = VARIANT_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "GetSyncableProperties")
    assert "issue #886" in block
    assert '"LexemeForm"' in block or "'LexemeForm'" in block
    assert "_GetTypedOwner" in block
    assert "LexemeFormOA" in block


def test_issue886_apply_syncable_properties_delegates_lexeme_form():
    text = VARIANT_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "ApplySyncableProperties")
    assert "LexemeForm" in block
    assert "LexEntry.ApplySyncableProperties" in block


def test_issue886_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #886"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "LexemeForm" in body
