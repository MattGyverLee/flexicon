#
#   test_issue792_discourse_delete_hvo_offline.py
#
#   Offline ratchet for issue #792 DiscourseOperations Delete HVO lookup.
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
    / "test_issue792_discourse_delete_hvo_live.py"
)


def _block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue792_delete_chart_uses_hvo_membership():
    block = _block(DISCOURSE.read_text(encoding="utf-8"), "DeleteChart")
    assert "issue #792" in block
    assert "int(chart.Hvo) == target_hvo" in block
    assert "ChartsOC.Remove(chart_obj)" not in block


def test_issue792_delete_row_uses_hvo_membership():
    block = _block(DISCOURSE.read_text(encoding="utf-8"), "DeleteRow")
    assert "issue #792" in block
    assert "int(row.Hvo) == target_hvo" in block
    assert "RowsOS.Remove(row_obj)" not in block


def test_issue792_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #792"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "DeleteChart" in body
    assert "DeleteRow" in body
