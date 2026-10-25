#
#   test_issue744_lexreference_complex_entries_hvo_offline.py
#
#   Offline ratchet for issue #744 LexReferenceOperations complex-form getters.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LEXREF_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexReferenceOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue744_lexreference_complex_entries_hvo_live.py"
)


def _method_block(text: str, method_name: str) -> str:
    start = text.index(f"def {method_name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue744_get_complex_form_entries_dedupes_by_hvo():
    source = LEXREF_OPS.read_text(encoding="utf-8")
    block = _method_block(source, "GetComplexFormEntries")
    assert "issue #744" in block
    assert "other_target not in complex_forms" not in block
    assert "cf.Hvo == other_hvo" in block


def test_issue744_get_component_entries_dedupes_by_hvo():
    source = LEXREF_OPS.read_text(encoding="utf-8")
    block = _method_block(source, "GetComponentEntries")
    assert "issue #744" in block
    assert "other_target not in components" not in block
    assert "comp.Hvo == other_hvo" in block


def test_issue744_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #744"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetComplexFormEntries" in body
    assert "GetComponentEntries" in body
