#
#   test_issue678_annotationdef_delete_hvo_offline.py
#
#   Offline ratchet for issue #678 AnnotationDef Delete HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ANNO_DEF_OPS = REPO_ROOT / "flexicon" / "code" / "System" / "AnnotationDefOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue678_annotationdef_delete_hvo_live.py"
)


def _delete_block(text: str) -> str:
    start = text.index("def Delete(self, anno_def):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue678_delete_uses_hvo_membership():
    block = _delete_block(ANNO_DEF_OPS.read_text(encoding="utf-8"))
    assert "issue #678" in block
    assert "poss.Hvo == target_hvo" in block
    assert "sub.Hvo == target_hvo" in block
    assert "anno_def in owner.PossibilitiesOS" not in block
    assert "anno_def in owner.SubPossibilitiesOS" not in block


def test_issue678_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #678"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
