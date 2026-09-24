#
#   test_issue360_datanotebook_gsp_offline.py
#
#   Offline regression lock for issue #360: GetSyncableProperties member names
#   on IRnGenericRec (TypeRA / StatusRA / ConfidenceRA / DateOfEvent).
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DATANB_OPS = REPO_ROOT / "flexicon" / "code" / "Notebook" / "DataNotebookOperations.py"


def _method_body(source: str, method_name: str) -> str:
    match = re.search(
        rf"def {method_name}\(.*?(?=\n    def |\n    # ---|\nclass |\Z)",
        source,
        re.DOTALL,
    )
    assert match is not None, f"{method_name} not found"
    return match.group(0)


def test_datanotebook_gsp_uses_irngenericrec_ra_members():
    source = DATANB_OPS.read_text(encoding="utf-8")
    body = _method_body(source, "GetSyncableProperties")
    for member in ("TypeRA", "StatusRA", "ConfidenceRA", "DateOfEvent"):
        assert member in body, f"expected {member} in GetSyncableProperties"


def test_datanotebook_gsp_does_not_use_phantom_bare_type_status_confidence():
    source = DATANB_OPS.read_text(encoding="utf-8")
    body = _method_body(source, "GetSyncableProperties")
    phantom_hasattr = re.findall(r'hasattr\(record,\s*["\'](\w+)["\']\)', body)
    assert "Type" not in phantom_hasattr
    assert "Status" not in phantom_hasattr
    assert "Confidence" not in phantom_hasattr
