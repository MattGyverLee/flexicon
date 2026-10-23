#
#   test_issue666_annotationdef_duplicate_hvo_offline.py
#
#   Offline ratchet for issue #666 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ANNO_OPS = REPO_ROOT / "flexicon" / "code" / "System" / "AnnotationDefOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue666_annotationdef_duplicate_hvo_live.py"
)


def _duplicate_block(text: str) -> str:
    start = text.index("def Duplicate")
    next_def = text.find("\n    def _DuplicateSubDefInto", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue666_duplicate_insert_after_uses_hvo_index():
    block = _duplicate_block(ANNO_OPS.read_text(encoding="utf-8"))
    assert "issue #666" in block
    assert "poss.Hvo == target_hvo" in block
    assert "PossibilitiesOS.IndexOf(source)" not in block
    assert "SubPossibilitiesOS.IndexOf(source)" not in block


def test_issue666_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #666"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Duplicate" in body
