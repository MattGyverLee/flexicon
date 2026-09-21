#
#   test_352_note_live.py
#
#   Live regression coverage for issue #352 (Note face): notes have no
#   Source multistring -- the author is the SourceRA agent reference.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

pytestmark = pytest.mark.requires_live_project


class Test352NoteAuthorReference:
    @pytest.mark.live_phase("NoteOperations", "add")
    def test_author_name_find_or_create(self, target_sandbox):
        notes = target_sandbox.Notes
        entry = target_sandbox.LexEntry.Create(lexeme_form="TEST_352author")
        try:
            note = notes.Create(entry, "Review needed")
            assert notes.GetAuthor(note) == ""
            notes.SetAuthor(note, "TEST_352 Author")
            assert notes.GetAuthor(note) == "TEST_352 Author"
            # Second note reuses the same agent (find, not duplicate).
            note2 = notes.Create(entry, "Second look")
            notes.SetAuthor(note2, "TEST_352 Author")
            assert notes.GetAuthor(note2) == "TEST_352 Author"
            agents = [
                a.Guid for a in target_sandbox.Agents.GetAll()
                if target_sandbox.Agents.GetName(a) == "TEST_352 Author"
            ]
            assert len(agents) == 1
            props = notes.GetSyncableProperties(note)
            assert props["Source"] == str(note.SourceRA.Guid)
        finally:
            target_sandbox.LexEntry.Delete(entry)
        for agent in list(target_sandbox.Agents.GetAll()):
            if target_sandbox.Agents.GetName(agent) == "TEST_352 Author":
                target_sandbox.Agents.Delete(agent)

    @pytest.mark.live_phase("NoteOperations", "add")
    def test_author_agent_object_and_clear(self, target_sandbox):
        notes = target_sandbox.Notes
        entry = target_sandbox.LexEntry.Create(lexeme_form="TEST_352author2")
        try:
            note = notes.Create(entry, "Review needed")
            agent = target_sandbox.Agents.Create("TEST_352 AgentObj")
            try:
                notes.SetAuthor(note, agent)
                assert notes.GetAuthor(note) == "TEST_352 AgentObj"
                notes.SetAuthor(note, "")
                assert notes.GetAuthor(note) == ""
                assert note.SourceRA is None
            finally:
                target_sandbox.Agents.Delete(agent)
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("NoteOperations", "read")
    def test_annotation_wrapper_author(self, target_sandbox):
        from flexicon.code.Notebook.annotation import Annotation
        notes = target_sandbox.Notes
        entry = target_sandbox.LexEntry.Create(lexeme_form="TEST_352author3")
        try:
            note = notes.Create(entry, "Review needed")
            assert Annotation(note).author == ""
            notes.SetAuthor(note, "TEST_352 Wrapped")
            assert Annotation(note).author == "TEST_352 Wrapped"
        finally:
            target_sandbox.LexEntry.Delete(entry)
        for agent in list(target_sandbox.Agents.GetAll()):
            if target_sandbox.Agents.GetName(agent) == "TEST_352 Wrapped":
                target_sandbox.Agents.Delete(agent)
