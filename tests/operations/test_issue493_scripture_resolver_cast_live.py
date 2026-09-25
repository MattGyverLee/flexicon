#
#   test_issue493_scripture_resolver_cast_live.py
#
#   Live gate for issue #493 Scripture HVO resolver casts.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def _first_book_with_sections(sandbox):
    books = list(sandbox.ScrBooks.GetAll())
    for book in books:
        sections = list(sandbox.ScrSections.GetAll(book))
        if sections:
            return book, sections[0]
    return None, None


@pytest.mark.requires_live_project
class TestIssue493ScriptureResolverHvoGate:
    """
    Each resolver feeds subtype-only collections (SectionsOS, ContentOA,
    FootnotesOS). HVO inputs must cast before those members are read.
    """

    @pytest.mark.live_phase("ScrSectionOperations", "read")
    def test_sections_getall_via_book_hvo(self, sena3_sandbox):
        sandbox = sena3_sandbox
        book, _section = _first_book_with_sections(sandbox)
        if book is None:
            pytest.skip("Sena 3 sandbox has no Scripture book with sections")
        hvo = book.Hvo
        assert isinstance(hvo, int), (
            "test setup error: hvo must be a genuine Python int"
        )
        bare = sandbox.Object(hvo)
        assert not hasattr(bare, "SectionsOS"), (
            "precondition failed: SectionsOS reachable on bare ICmObject view"
        )

        by_obj = list(sandbox.ScrSections.GetAll(book))
        by_hvo = list(sandbox.ScrSections.GetAll(hvo))
        assert by_hvo == by_obj

    @pytest.mark.live_phase("ScrTxtParaOperations", "read")
    def test_paragraphs_getall_via_section_hvo(self, sena3_sandbox):
        sandbox = sena3_sandbox
        _book, section = _first_book_with_sections(sandbox)
        if section is None:
            pytest.skip("Sena 3 sandbox has no Scripture section")
        hvo = section.Hvo
        assert isinstance(hvo, int), (
            "test setup error: hvo must be a genuine Python int"
        )
        bare = sandbox.Object(hvo)
        assert not hasattr(bare, "ContentOA"), (
            "precondition failed: ContentOA reachable on bare ICmObject view"
        )

        by_obj = list(sandbox.ScrTxtParas.GetAll(section))
        by_hvo = list(sandbox.ScrTxtParas.GetAll(hvo))
        assert by_hvo == by_obj

    @pytest.mark.live_phase("ScrNoteOperations", "read")
    def test_notes_getall_via_book_hvo(self, sena3_sandbox):
        sandbox = sena3_sandbox
        books = list(sandbox.ScrBooks.GetAll())
        if not books:
            pytest.skip("Sena 3 sandbox has no Scripture books")
        book = books[0]
        hvo = book.Hvo
        assert isinstance(hvo, int), (
            "test setup error: hvo must be a genuine Python int"
        )
        bare = sandbox.Object(hvo)
        assert not hasattr(bare, "FootnotesOS"), (
            "precondition failed: FootnotesOS reachable on bare ICmObject view"
        )

        by_obj = list(sandbox.ScrNotes.GetAll(book))
        by_hvo = list(sandbox.ScrNotes.GetAll(hvo))
        assert by_hvo == by_obj

    @pytest.mark.live_phase("ScrAnnotationsOperations", "read")
    def test_annotations_getforbook_via_book_hvo(self, sena3_sandbox):
        sandbox = sena3_sandbox
        books = list(sandbox.ScrBooks.GetAll())
        if not books:
            pytest.skip("Sena 3 sandbox has no Scripture books")
        book = books[0]
        hvo = book.Hvo
        assert isinstance(hvo, int), (
            "test setup error: hvo must be a genuine Python int"
        )
        bare = sandbox.Object(hvo)
        assert not hasattr(bare, "FootnotesOS"), (
            "precondition failed: FootnotesOS reachable on bare ICmObject view"
        )

        by_obj = sandbox.ScrAnnotations.GetForBook(book)
        by_hvo = sandbox.ScrAnnotations.GetForBook(hvo)
        assert by_hvo == by_obj
