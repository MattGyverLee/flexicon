#
#   test_person_syncable_properties_offline.py
#
#   Offline coverage for issue #362 without importing flexicon (no LCM on Linux CI).
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PERSON_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "PersonOperations.py"


def _method_body(source: str, method_name: str) -> str:
    match = re.search(
        rf"def {method_name}\(.*?(?=\n    def |\n    # ---|\nclass |\Z)",
        source,
        re.DOTALL,
    )
    assert match is not None, f"{method_name} not found"
    return match.group(0)


def test_person_get_syncable_properties_does_not_read_languagesrc():
    source = PERSON_OPS.read_text(encoding="utf-8")
    assert "def GetSyncableProperties" in source
    body = _method_body(source, "GetSyncableProperties")
    assert "LanguagesRC" not in body
    assert '"Languages"' not in body and "'Languages'" not in body


def test_person_get_syncable_properties_still_emits_real_rc_fields():
    source = PERSON_OPS.read_text(encoding="utf-8")
    body = _method_body(source, "GetSyncableProperties")
    assert "PositionsRC" in body
    assert "PlacesOfResidenceRC" in body
