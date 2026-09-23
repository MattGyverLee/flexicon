#
#   test_issue302_328_datanotebook_offline.py
#
#   Offline regression for issues #302, #328, and #261
#   (DataNotebookOperations record CRUD and Title/content paths).
#
#   Copyright 2026
#

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATANB_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "DataNotebookOperations.py"


def _source() -> str:
    return DATANB_OPS.read_text(encoding="utf-8")


def test_issue302_328_ruling_document_exists():
    ruling = REPO_ROOT / "specs" / "302-datanotebook-records" / "rulings.md"
    assert ruling.is_file()
    text = ruling.read_text(encoding="utf-8")
    assert "ResearchNotebookOA.RecordsOC" in text
    assert "project.Object" in text


def test_issue302_no_repository_records_oc():
    """Create/Delete/Duplicate must not use repos.RecordsOC (#302)."""
    source = _source()
    assert "repos.RecordsOC" not in source
    assert "ResearchNotebookOA.RecordsOC" in source


def test_issue302_get_record_object_uses_flex_project_object():
    """__GetRecordObject must use FLExProject.Object(), not LcmCache.GetObject (#302/#261)."""
    source = _source()
    block = source.split("def __GetRecordObject(self, record_or_hvo):", 1)[1]
    block = block.split("\n    def ", 1)[0]
    assert "self.project.Object(hvo)" in block
    assert "self.project.project.GetObject" not in block


def test_issue328_title_write_is_direct_assignment():
    """Title is bare ITsString -- assign, do not call set_String (#328)."""
    source = _source()
    create_block = source.split("def Create(self, title, content=None", 1)[1]
    create_block = create_block.split("\n    def ", 1)[0]
    assert "Title.set_String" not in create_block
    assert "record.Title = self._MakeTsString" in create_block

    set_title_block = source.split("def SetTitle(self, record_or_hvo, title", 1)[1]
    set_title_block = set_title_block.split("\n    def ", 1)[0]
    assert "Title.set_String" not in set_title_block
    assert "record.Title = self._MakeTsString" in set_title_block


def test_issue328_no_text_member_on_record():
    """IRnGenericRec has no Text member -- content via DescriptionOA (#328)."""
    source = _source()
    assert "record.Text.set_String" not in source
    assert "CopyAlternatives(source.Text" not in source
    assert "_ReadRecordContent" in source
    assert "_SetRecordContent" in source

    dup_block = source.split("def Duplicate(self, record_or_hvo", 1)[1]
    dup_block = dup_block.split("\n    def ", 1)[0]
    assert "CopyAlternatives(source.Text" not in dup_block
    assert "_CopyRecordContent" in dup_block
