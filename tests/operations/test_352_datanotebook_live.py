#
#   test_352_datanotebook_live.py
#
#   Live regression coverage for issue #352 (DataNotebook face):
#   IRnGenericRec.Title is a bare ITsString (not IMultiString) and there
#   is no Text member -- body content lives in DescriptionOA paragraphs.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_TITLE = "TEST_352 title"
TEST_CONTENT = "First paragraph.\nSecond paragraph."


class Test352DataNotebookTitleContentRoundTrip:
    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_create_readback_title_content(self, target_sandbox):
        op = target_sandbox.DataNotebook
        rec = op.Create(TEST_TITLE, content=TEST_CONTENT)
        try:
            assert op.GetTitle(rec) == TEST_TITLE
            assert op.GetContent(rec) == TEST_CONTENT
            assert op.Find(TEST_TITLE) is not None
            props = op.GetSyncableProperties(rec)
            assert props["Title"] == TEST_TITLE
            assert props["Text"] == TEST_CONTENT
        finally:
            op.Delete(rec)
        assert op.Find(TEST_TITLE) is None

    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_set_title_content_roundtrip(self, target_sandbox):
        op = target_sandbox.DataNotebook
        rec = op.Create(TEST_TITLE)
        try:
            assert op.GetContent(rec) == ""
            op.SetTitle(rec, TEST_TITLE + " v2")
            assert op.GetTitle(rec) == TEST_TITLE + " v2"
            op.SetContent(rec, TEST_CONTENT)
            assert op.GetContent(rec) == TEST_CONTENT
            op.SetContent(rec, "")
            assert op.GetContent(rec) == ""
        finally:
            op.Delete(rec)

    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_duplicate_conserves_title_content(self, target_sandbox):
        op = target_sandbox.DataNotebook
        rec = op.Create(TEST_TITLE, content=TEST_CONTENT)
        try:
            dup = op.Duplicate(rec, deep=True)
            try:
                assert op.GetTitle(dup) == TEST_TITLE
                assert op.GetContent(dup) == TEST_CONTENT
                is_diff, _ = op.CompareTo(rec, dup)
                assert not is_diff
            finally:
                op.Delete(dup)
        finally:
            op.Delete(rec)

    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_subrecord_title_content(self, target_sandbox):
        op = target_sandbox.DataNotebook
        rec = op.Create(TEST_TITLE)
        try:
            sub = op.CreateSubRecord(rec, TEST_TITLE + " sub", content=TEST_CONTENT)
            assert op.GetTitle(sub) == TEST_TITLE + " sub"
            assert op.GetContent(sub) == TEST_CONTENT
        finally:
            op.Delete(rec)
