#
#   test_issue519_paragraph_get_owning_text_offline.py
#
#   Offline ratchet for issue #519 GetOwningText owner chain.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PARAGRAPH_OPS = (
    REPO_ROOT / "flexicon" / "code" / "TextsWords" / "ParagraphOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue519_paragraph_get_owning_text_live.py"
)


def _get_owning_text_block(text: str) -> str:
    start = text.index("def GetOwningText")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _duplicate_block(text: str) -> str:
    start = text.index("def Duplicate")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue519_get_owning_text_uses_typed_owner_and_gettext():
    source = PARAGRAPH_OPS.read_text(encoding="utf-8")
    block = _get_owning_text_block(source)
    assert "_GetTypedOwner(para_obj)" in block
    assert "__GetTextObject(st_text.Owner)" in block
    assert "IText(st_text.Owner)" not in block
    assert "issue #519" in block


def test_issue519_duplicate_delegates_parent_text_to_get_owning_text():
    block = _duplicate_block(PARAGRAPH_OPS.read_text(encoding="utf-8"))
    assert "GetOwningText(para_obj)" in block
    assert "IText(owner.Owner)" not in block


def test_issue519_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #519"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetOwningText" in body
