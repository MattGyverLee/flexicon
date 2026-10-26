#
#   test_issue674_scrsection_moveto_hvo_offline.py
#
#   Offline ratchet for issue #674 MoveTo same-book SectionsOS HVO index.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCR_SECTION_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Scripture" / "ScrSectionOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue674_scrsection_moveto_hvo_live.py"
)


def _move_to_block(text: str) -> str:
    start = text.index("def MoveTo")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue674_move_to_uses_hvo_index():
    block = _move_to_block(SCR_SECTION_OPS.read_text(encoding="utf-8"))
    assert "issue #674" in block
    assert "member.Hvo == section_hvo" in block
    assert "SectionsOS.IndexOf(section)" not in block


def test_issue674_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #674"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "MoveTo" in body
