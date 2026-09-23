#
#   test_issue361_annotationdef_gsp_offline.py
#
#   Offline regression for issue #361: AnnotationDefOperations
#   GetSyncableProperties must use real ICmAnnotationDefn members.
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ANNO_OPS = REPO_ROOT / "flexicon" / "code" / "System" / "AnnotationDefOperations.py"


def _gsp_body(source: str) -> str:
    match = re.search(
        r"def GetSyncableProperties\(.*?(?=\n    def |\nclass |\Z)",
        source,
        re.DOTALL,
    )
    assert match is not None
    return match.group(0)


def test_get_syncable_properties_uses_baseline_members():
    source = ANNO_OPS.read_text(encoding="utf-8")
    body = _gsp_body(source)
    assert "InstanceOfSignature" in body
    assert "AllowsInstanceOf" in body
    assert "anno_def.Multi" in body
    assert 'hasattr(anno_def, "AnnotationType")' not in body
    assert 'hasattr(anno_def, "InstanceOf")' not in body
    assert 'hasattr(anno_def, "AllowsMultiple")' not in body
    assert 'props["AnnotationType"]' not in body
