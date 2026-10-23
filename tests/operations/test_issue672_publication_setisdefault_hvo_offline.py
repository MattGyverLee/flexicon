#
#   test_issue672_publication_setisdefault_hvo_offline.py
#
#   Offline ratchet for issue #672 SetIsDefault HVO index lookup.
#
#   Copyright 2026
#

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PUBLICATION_OPS = REPO_ROOT / "flexicon" / "code" / "Lists" / "PublicationOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue672_publication_setisdefault_hvo_live.py"
)


def _set_is_default_block(text: str) -> str:
    start = text.index("def SetIsDefault")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue672_set_is_default_uses_hvo_index():
    block = _set_is_default_block(PUBLICATION_OPS.read_text(encoding="utf-8"))
    assert "issue #672" in block
    assert "member.Hvo == target_hvo" in block
    assert "IndexOf(publication)" not in block
    assert "publication not in seq" not in block


def test_issue672_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #672"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "SetIsDefault" in body


def test_issue672_ruling_document_exists():
    ruling = REPO_ROOT / "specs" / "672-publication-setisdefault-hvo" / "rulings.md"
    assert ruling.is_file()
    text = ruling.read_text(encoding="utf-8")
    assert "#672" in text
    assert "SetIsDefault" in text
