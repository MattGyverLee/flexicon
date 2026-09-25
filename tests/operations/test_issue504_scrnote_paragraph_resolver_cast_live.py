#
#   test_issue504_scrnote_paragraph_resolver_cast_live.py
#
#   Live gate for issue #504 ScrNoteOperations paragraph HVO resolver cast.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest
from SIL.LCModel import IScrTxtPara

pytestmark = pytest.mark.requires_live_project


def _first_book_section_para(sandbox):
    for book in sandbox.ScrBooks.GetAll():
        for section in sandbox.ScrSections.GetAll(book):
            paras = list(sandbox.ScrTxtParas.GetAll(section))
            if paras:
                return book, section, paras[0]
    return None, None, None


@pytest.mark.requires_live_project
class TestIssue504ScrNoteParagraphHvoGate:
    """Create() resolves paragraph_or_hvo via __ResolveParagraph."""

    @pytest.mark.live_phase("ScrNoteOperations", "write")
    def test_create_accepts_paragraph_hvo(self, sena3_sandbox):
        sandbox = sena3_sandbox
        if not sandbox.writeEnabled:
            pytest.skip("sandbox is read-only")

        book, _section, para = _first_book_section_para(sandbox)
        if para is None:
            pytest.skip("Sena 3 sandbox has no Scripture paragraph")

        book_hvo = book.Hvo
        para_hvo = para.Hvo
        assert isinstance(book_hvo, int) and isinstance(para_hvo, int), (
            "test setup error: hvos must be genuine Python ints"
        )
        bare = sandbox.Object(para_hvo)
        assert getattr(bare, "ClassName", None) == "ScrTxtPara"
        assert not isinstance(bare, IScrTxtPara), (
            "precondition failed: bare ICmObject view should fail isinstance IScrTxtPara"
        )

        note = None
        try:
            note = sandbox.ScrNotes.Create(
                book_hvo,
                para_hvo,
                "TEST_504 paragraph HVO resolver gate",
            )
            assert note is not None
        finally:
            if note is not None:
                sandbox.ScrNotes.Delete(note)
