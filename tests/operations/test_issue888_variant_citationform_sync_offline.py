#
#   test_issue888_variant_citationform_sync_offline.py
#
#   Offline ratchet for issue #888 owning-entry CitationForm sync fields.
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
    / "test_issue888_variant_citationform_sync_live.py"
)


def _method_block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue888_get_syncable_properties_emits_citation_form():
    text = VARIANT_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "GetSyncableProperties")
    assert "issue #888" in block
    assert '"CitationForm"' in block or "'CitationForm'" in block
    assert "CitationForm.get_String" in block


def test_issue888_apply_syncable_properties_delegates_citation_form():
    text = VARIANT_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "ApplySyncableProperties")
    assert "CitationForm" in block
    assert "LexEntry.ApplySyncableProperties" in block


def test_issue888_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #888"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "CitationForm" in body
