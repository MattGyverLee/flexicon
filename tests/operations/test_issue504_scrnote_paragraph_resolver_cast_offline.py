#
#   test_issue504_scrnote_paragraph_resolver_cast_offline.py
#
#   Offline ratchet for issue #504 ScrNoteOperations paragraph HVO resolver cast.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRNOTE_OPS = REPO_ROOT / "flexicon" / "code" / "Scripture" / "ScrNoteOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue504_scrnote_paragraph_resolver_cast_live.py"
)


def test_issue504_paragraph_resolver_uses_cast_to_concrete():
    text = SCRNOTE_OPS.read_text(encoding="utf-8")
    assert "from ..lcm_casting import cast_to_concrete" in text
    assert "def __ResolveParagraph" in text
    helper_start = text.index("def __ResolveParagraph")
    next_def = text.find("\n    def ", helper_start + 1)
    block = text[helper_start:next_def] if next_def != -1 else text[helper_start:]
    assert "cast_to_concrete(self.project.Object" in block
    assert "return cast_to_concrete(para_or_hvo)" in block
    assert "return self.project.Object(" not in block
    assert 'ClassName", None) == "ScrTxtPara"' in block


def test_issue504_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #504"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "Create" in text
    assert "isinstance(book_hvo, int)" in text
    assert "requires_live_project" in text
