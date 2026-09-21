#
#   test_352_scrbook_live.py
#
#   Live regression coverage for the sweep-doc follow-up to issue #352
#   (ScrBook face): IScrBook has no Title member -- the book name is the
#   Name MultiUnicode.
#
#   Target has no Scripture, so this runs against the installed
#   Tlachichilco Tepehua-NT orthography project: reads open read-only,
#   and the write path creates a book under a free canonical number with
#   strict finally-cleanup plus a zero-residue assertion.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

from flexicon.code.FLExProject import FLExProject
from flexicon.code.Scripture.ScrBookOperations import ScrBookOperations

pytestmark = pytest.mark.requires_live_project

FOREIGN_PROJECT = "Tlachichilco Tepehua-NT orthography"


def _open(write_enabled):
    import sys
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    project = FLExProject()
    try:
        # undoable=False matches the house live fixtures (headless
        # UnitOfWork commit crashes; the session envelope commits).
        project.OpenProject(FOREIGN_PROJECT, writeEnabled=write_enabled, undoable=False)
    except Exception as e:
        pytest.skip(f"Cannot open {FOREIGN_PROJECT}: {e}")
    return project


@pytest.fixture()
def foreign_readonly():
    project = _open(False)
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


@pytest.fixture()
def foreign_writable():
    project = _open(True)
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


class Test352ScrBookNameRetarget:
    @pytest.mark.live_phase("ScrBookOperations", "read")
    def test_read_real_book(self, foreign_readonly):
        op = foreign_readonly.ScrBooks
        assert isinstance(op, ScrBookOperations)
        book = op.Find(40)
        assert book is not None
        title = op.GetTitle(book)
        assert isinstance(title, str) and title != ""
        assert op.FindByName(title) is not None
        assert op.Find(999) is None

    @pytest.mark.live_phase("ScrBookOperations", "add")
    def test_create_set_delete_roundtrip(self, foreign_writable):
        op = foreign_writable.ScrBooks
        used = {b.CanonicalNum for b in op.GetAll()}
        free = next((n for n in range(1, 67) if n not in used), None)
        if free is None:
            pytest.skip("No free canonical book number")
        before = {b.Hvo for b in op.GetAll()}
        book = op.Create(free, "TEST_352 book")
        try:
            assert op.GetTitle(book) == "TEST_352 book"
            op.SetTitle(book, "TEST_352 relabel")
            assert op.GetTitle(book) == "TEST_352 relabel"
        finally:
            op.Delete(book.Hvo)
        after = {b.Hvo for b in op.GetAll()}
        assert after == before
