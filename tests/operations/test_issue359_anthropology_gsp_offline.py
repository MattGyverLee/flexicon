#
#   test_issue359_anthropology_gsp_offline.py
#
#   Offline regression for issue #359 (Anthropology GetSyncableProperties).
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ANTHRO_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "AnthropologyOperations.py"


def test_issue359_ruling_document_exists():
    ruling = REPO_ROOT / "specs" / "359-anthropology-gsp" / "rulings.md"
    assert ruling.is_file()
    text = ruling.read_text(encoding="utf-8")
    assert "Abbreviation" in text
    assert "CategoryRA" in text
