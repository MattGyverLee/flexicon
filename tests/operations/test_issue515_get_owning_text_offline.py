#
#   test_issue515_get_owning_text_offline.py
#
#   Offline ratchet for issue #515 GetOwningText owner-chain cast.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DISCOURSE = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "DiscourseOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue515_get_owning_text_live.py"
)


def _get_owning_text_block(text: str) -> str:
    start = text.index("def GetOwningText")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue515_get_owning_text_uses_typed_owner_and_gettext():
    block = _get_owning_text_block(DISCOURSE.read_text(encoding="utf-8"))
    assert "_GetTypedOwner(chart_obj)" in block
    assert "__GetTextObject(st_text.Owner)" in block
    assert "chart_obj.Owner" not in block
    assert "issue #515" in block


def test_issue515_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #515"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetOwningText" in body
