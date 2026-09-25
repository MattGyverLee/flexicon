#
#   test_issue513_discourse_owner_cast_offline.py
#
#   Offline ratchet for issue #513 DiscourseOperations owner cast on
#   delete/duplicate write paths.
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
    / "test_issue513_discourse_owner_cast_live.py"
)


def _block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue513_delete_chart_uses_get_typed_owner():
    block = _block(DISCOURSE.read_text(encoding="utf-8"), "DeleteChart")
    assert "_GetTypedOwner(chart_obj)" in block
    assert "chart_obj.Owner" not in block
    assert "ChartsOC" in block


def test_issue513_delete_row_uses_get_typed_owner():
    block = _block(DISCOURSE.read_text(encoding="utf-8"), "DeleteRow")
    assert "_GetTypedOwner(row_obj)" in block
    assert "row_obj.Owner" not in block
    assert "RowsOS" in block


def test_issue513_duplicate_uses_get_typed_owner():
    block = _block(DISCOURSE.read_text(encoding="utf-8"), "Duplicate")
    assert "_GetTypedOwner(source)" in block
    assert "source.Owner" not in block
    assert "ChartsOC" in block


def test_issue513_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #513"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "DeleteChart" in body
