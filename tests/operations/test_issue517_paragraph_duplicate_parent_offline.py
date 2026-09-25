#
#   test_issue517_paragraph_duplicate_parent_offline.py
#
#   Offline ratchet for issue #517 Duplicate parent-text owner chain.
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
    / "test_issue517_paragraph_duplicate_parent_live.py"
)


def _duplicate_block(text: str) -> str:
    start = text.index("def Duplicate")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue517_duplicate_routes_sttext_owner_through_gettext():
    source = PARAGRAPH_OPS.read_text(encoding="utf-8")
    block = _duplicate_block(source)
    assert "_GetTypedOwner(para_obj)" in block
    assert "GetOwningText(para_obj)" in block
    assert "IText(owner.Owner)" not in block
    owning = source[source.index("def GetOwningText") : source.index("def InsertAt")]
    assert "__GetTextObject(st_text.Owner)" in owning


def test_issue517_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #517"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Duplicate" in body
