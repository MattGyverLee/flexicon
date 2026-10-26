#
#   test_issue658_note_duplicate_hvo_offline.py
#
#   Offline ratchet for issue #658 Duplicate insert_after HVO index lookup.
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
    / "test_issue658_note_duplicate_hvo_live.py"
)


def _note_ops_text() -> str:
    return NOTE_OPS.read_text(encoding="utf-8")


def test_issue658_attach_reply_insert_after_uses_hvo_index():
    text = _note_ops_text()
    start = text.index("def __AttachReply")
    block = text[start : text.index("\n    def ", start + 1)]
    assert "issue #658" in block
    assert "resp.Hvo == target_hvo" in block
    assert "ResponsesOS.IndexOf(after_source)" not in block


def test_issue658_duplicate_responses_os_uses_hvo_index():
    text = _note_ops_text()
    start = text.index("def Duplicate")
    block = text[start : text.index("\n    @OperationsMethod", start + 1)]
    assert "issue #658" in block
    assert "resp.Hvo == target_hvo" in block
    assert "ResponsesOS.IndexOf(source)" not in block


def test_issue658_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #658"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Duplicate" in body
