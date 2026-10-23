#
#   test_issue680_note_delete_hvo_live.py
#
#   Live verification for issue #680 NoteOperations Delete HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def test_issue680_delete_removes_from_owner_by_hvo(target_project):
    """Delete removes a note after re-fetching by HVO."""
    project = target_project
    lexeme = "TEST_680_delete_hvo"
    entry = project.LexEntry.Create(lexeme_form=lexeme)
    try:
        note = project.Note.Create(entry, "TEST_680 body")
        hvo = note.Hvo
        bare_view = project.Object(hvo)
        project.Note.Delete(bare_view)
        remaining = list(project.Note.GetAll(entry))
        assert all(n.Hvo != hvo for n in remaining)
    finally:
        for n in list(project.Note.GetAll(entry)):
            project.Note.Delete(n)
        found = project.LexEntry.Find(lexeme)
        if found is not None:
            project.LexEntry.Delete(found)
