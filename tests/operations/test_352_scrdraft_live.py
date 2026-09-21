#
#   test_352_scrdraft_live.py
#
#   Live regression coverage for issue #352 (ScrDraft face):
#   IScrDraft.Description is a scalar String (not a multistring).
#
#   Target has no Scripture, so the read path runs against the installed
#   Tlachichilco Tepehua-NT orthography project (read-only open) and the
#   write path creates a TEST_-prefixed draft there with strict
#   finally-cleanup plus a zero-residue assertion.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

from flexicon.code.FLExProject import FLExProject
from flexicon.code.Scripture.ScrDraftOperations import ScrDraftOperations

pytestmark = pytest.mark.requires_live_project

FOREIGN_PROJECT = "Tlachichilco Tepehua-NT orthography"


@pytest.fixture()
def foreign_readonly():
    import sys
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    project = FLExProject()
    try:
        project.OpenProject(FOREIGN_PROJECT, writeEnabled=False)
    except Exception as e:
        pytest.skip(f"Cannot open {FOREIGN_PROJECT}: {e}")
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


@pytest.fixture()
def foreign_writable():
    import sys
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    project = FLExProject()
    try:
        # undoable=False matches the house live fixtures: per-operation
        # UnitOfWork commit crashes headless (no ISynchronizeInvoke for
        # prop-change notifications); the session envelope commits.
        project.OpenProject(FOREIGN_PROJECT, writeEnabled=True, undoable=False)
    except Exception as e:
        pytest.skip(f"Cannot open {FOREIGN_PROJECT}: {e}")
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


class Test352ScrDraftScalarDescription:
    @pytest.mark.live_phase("ScrDraftOperations", "read")
    def test_read_real_draft(self, foreign_readonly):
        # project.ScrDrafts accessor must exist (was missing entirely).
        op = foreign_readonly.ScrDrafts
        assert isinstance(op, ScrDraftOperations)
        drafts = list(op.GetAll())
        assert len(drafts) >= 1
        assert op.GetDescription(drafts[0]) == "Last Standard Format Import"
        assert op.Find("standard format") is not None
        assert op.Find("ZZZ_NO_SUCH_DRAFT") is None

    @pytest.mark.live_phase("ScrDraftOperations", "add")
    def test_create_set_delete_roundtrip(self, foreign_writable):
        op = foreign_writable.ScrDrafts
        before = {d.Hvo for d in op.GetAll()}
        draft = op.Create("TEST_352 draft")
        try:
            assert op.GetDescription(draft) == "TEST_352 draft"
            assert op.Find("test_352 draft") is not None
            op.SetDescription(draft, "TEST_352 relabel")
            assert op.GetDescription(draft) == "TEST_352 relabel"
        finally:
            op.Delete(draft.Hvo)
        after = {d.Hvo for d in op.GetAll()}
        assert after == before
