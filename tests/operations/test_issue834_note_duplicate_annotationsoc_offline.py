#
#   test_issue834_note_duplicate_annotationsoc_offline.py
#
#   Offline ratchet for issue #834 Duplicate insert_after on AnnotationsOC.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NOTE_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "NoteOperations.py"
RULING = (
    REPO_ROOT
    / "specs"
    / "834-note-duplicate-annotationsoc"
    / "rulings.md"
)


def _note_ops_text() -> str:
    return NOTE_OPS.read_text(encoding="utf-8")


def test_issue834_ruling_file_exists():
    assert RULING.is_file(), "missing lex-lead ruling for #834"


def test_issue834_docstring_does_not_claim_universal_position():
    text = _note_ops_text()
    start = text.index("def Duplicate")
    block = text[start : text.index("\n    @OperationsMethod", start + 1)]
    assert "preserves the original note's position" not in block
    assert "issue #834" in block


def test_issue834_attach_reply_warns_on_unordered_insert_after():
    text = _note_ops_text()
    start = text.index("def __AttachReply")
    block = text[start : text.index("\n    def ", start + 1)]
    assert "issue #834" in block
    assert "logger.warning" in block
    assert "AnnotationsOC" in block


def test_issue834_duplicate_annotations_oc_warns_on_insert_after():
    text = _note_ops_text()
    start = text.index("def Duplicate")
    block = text[start : text.index("\n    @OperationsMethod", start + 1)]
    assert block.count("issue #834") >= 2
    assert "insert_after=True ignored for Duplicate on AnnotationsOC" in block
