#
#   test_issue508_text_resolver_offline.py
#
#   Offline ratchet for issue #508 text __GetTextObject cast alignment.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PARAGRAPH = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "ParagraphOperations.py"
DISCOURSE = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "DiscourseOperations.py"
TEXT_REF = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "TextOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue508_text_resolver_live.py"
)


def _gettext_block(text: str) -> str:
    start = text.index("def __GetTextObject")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue508_text_operations_reference_has_classname_cast():
    block = _gettext_block(TEXT_REF.read_text(encoding="utf-8"))
    assert 'ClassName", None) == "Text"' in block
    assert "issue #275" in block


def test_issue508_paragraph_gettext_matches_classname_pattern():
    block = _gettext_block(PARAGRAPH.read_text(encoding="utf-8"))
    assert 'ClassName", None) == "Text"' in block
    assert "issue #508" in block
    assert "return text_or_hvo" in block


def test_issue508_discourse_gettext_matches_classname_pattern():
    block = _gettext_block(DISCOURSE.read_text(encoding="utf-8"))
    assert 'ClassName", None) == "Text"' in block
    assert "issue #508" in block


def test_issue508_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #508"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Object(" in body
