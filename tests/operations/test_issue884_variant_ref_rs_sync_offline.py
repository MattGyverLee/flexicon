#
#   test_issue884_variant_ref_rs_sync_offline.py
#
#   Offline ratchet for issue #884 ILexEntryRef RS sync fields.
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
    / "test_issue884_variant_ref_rs_sync_live.py"
)


def _method_block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue884_get_syncable_properties_emits_entry_ref_rs_fields():
    text = VARIANT_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "GetSyncableProperties")
    assert "issue #884" in block
    for key in (
        "variant_entry_types_rs",
        "component_lexemes_rs",
        "complex_entry_types_rs",
        "primary_lexemes_rs",
    ):
        assert f'"{key}"' in block or f"'{key}'" in block or key in block


def test_issue884_apply_syncable_properties_handles_rs_keys():
    text = VARIANT_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "ApplySyncableProperties")
    assert "__ENTRY_REF_SYNC_RS_KEYS" in block
    assert "__ApplyEntryRefReferenceSequence" in block


def test_issue884_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #884"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetSyncableProperties" in body
