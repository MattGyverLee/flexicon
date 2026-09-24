#
#   test_issue323_note_replies_offline.py
#
#   Offline regression for issue #323 (note reply threading).
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NOTE_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "NoteOperations.py"
ANNOTATION_PY = REPO_ROOT / "flexicon" / "code" / "Notebook" / "annotation.py"


def test_issue323_ruling_document_exists():
    ruling = REPO_ROOT / "specs" / "323-note-replies" / "rulings.md"
    assert ruling.is_file()
    text = ruling.read_text(encoding="utf-8")
    assert "ResponsesOS" in text
    assert "BeginObjectRA" in text


def test_note_operations_no_phantom_repliesos_guards():
    text = NOTE_OPS.read_text(encoding="utf-8")
    assert "hasattr(parent, \"RepliesOS\")" not in text
    assert "hasattr(source, \"RepliesOS\")" not in text
    assert "hasattr(note, \"RepliesOS\")" not in text
    assert "hasattr(parent_note, \"RepliesOS\")" not in text
    assert "__IterDirectReplies" in text
    assert "__AttachReply" in text
    assert "ResponsesOS" in text


def test_annotation_wrapper_no_repliesos_guard():
    text = ANNOTATION_PY.read_text(encoding="utf-8")
    assert "hasattr(self._obj, \"RepliesOS\")" not in text
    assert "ResponsesOS" in text
    assert "BeginObjectRA" in text


def test_note_operations_documents_issue_323():
    text = NOTE_OPS.read_text(encoding="utf-8")
    assert re.search(r"issue #323", text, re.IGNORECASE)
