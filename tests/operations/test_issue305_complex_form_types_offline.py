#
#   test_issue305_complex_form_types_offline.py
#
#   Offline regression for issue #305: complex form type list accessor.
#
#   Copyright 2026
#

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LEX_ENTRY_OPS = _REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexEntryOperations.py"


class TestIssue305ComplexFormTypesOffline:
    def test_get_all_complex_form_types_reaches_complex_entry_types_oa(self):
        src = _LEX_ENTRY_OPS.read_text(encoding="utf-8")
        assert "def GetAllComplexFormTypes(self):" in src
        assert "ComplexEntryTypesOA" in src
        assert "cast_to_concrete" in src
        assert "SubPossibilitiesOS" in src

    def test_find_complex_form_type_searches_get_all(self):
        src = _LEX_ENTRY_OPS.read_text(encoding="utf-8")
        assert "def FindComplexFormType(self, name):" in src
        block = src.split("def FindComplexFormType(self, name):", 1)[1].split(
            "\n    def ", 1
        )[0]
        assert "GetAllComplexFormTypes()" in block
        assert "normalize_match_key" in block

    def test_issue305_ruling_document_exists(self):
        ruling = _REPO_ROOT / "specs" / "305-complex-form-types" / "rulings.md"
        assert ruling.is_file()
        text = ruling.read_text(encoding="utf-8")
        assert "GetAllComplexFormTypes" in text
        assert "FindComplexFormType" in text
