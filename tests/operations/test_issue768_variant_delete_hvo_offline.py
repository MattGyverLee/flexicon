#
#   test_issue768_variant_delete_hvo_offline.py
#
#   Offline ratchet for issue #768 Delete EntryRefsOS HVO membership.
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
    / "test_issue768_variant_delete_hvo_live.py"
)


def _delete_block(text: str) -> str:
    start = text.index("def Delete(")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue768_delete_uses_hvo_membership():
    block = _delete_block(VARIANT_OPS.read_text(encoding="utf-8"))
    assert "issue #768" in block
    assert "int(ref.Hvo) == target_hvo" in block
    assert "EntryRefsOS.Remove(variant)" not in block


def test_issue768_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #768"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
