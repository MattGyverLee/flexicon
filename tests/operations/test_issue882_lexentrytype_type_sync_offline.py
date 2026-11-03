#
#   test_issue882_lexentrytype_type_sync_offline.py
#
#   Offline ratchet for issue #882 LexEntryType multistring sync fields.
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
    / "test_issue882_lexentrytype_type_sync_live.py"
)


def _method_block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue882_get_type_syncable_properties_emits_lex_entry_type_fields():
    text = VARIANT_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "GetTypeSyncableProperties")
    assert "issue #882" in block
    assert 'class_name == "LexEntryType"' in block
    for field in ("Name", "Abbreviation", "Description", "ReverseAbbr"):
        assert field in block
    assert "GlossPrepend" in block and "issue #878" in block


def test_issue882_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #882"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetTypeSyncableProperties" in body
