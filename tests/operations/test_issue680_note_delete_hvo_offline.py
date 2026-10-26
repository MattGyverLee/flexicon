#
#   test_issue680_note_delete_hvo_offline.py
#
#   Offline ratchet for issue #680 NoteOperations Delete HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NOTE_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "NoteOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue680_note_delete_hvo_live.py"
)


def _delete_block(text: str) -> str:
    start = text.index("def Delete(self, note):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue680_delete_uses_hvo_membership():
    block = _delete_block(NOTE_OPS.read_text(encoding="utf-8"))
    assert "issue #680" in block
    assert "ann.Hvo == target_hvo" in block
    assert "resp.Hvo == target_hvo" in block
    assert "note in owner.AnnotationsOC" not in block
    assert "note in owner.ResponsesOS" not in block


def test_issue680_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #680"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
