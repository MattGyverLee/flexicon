#
#   test_issue766_lexref_deletetype_hvo_offline.py
#
#   Offline ratchet for issue #766 LexReferenceOperations DeleteType HVO membership.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LEXREF_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexReferenceOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue766_lexref_deletetype_hvo_live.py"
)


def _delete_type_block(text: str) -> str:
    start = text.index("def DeleteType(self, ref_type_or_hvo)")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue766_delete_type_uses_hvo_membership():
    block = _delete_type_block(LEXREF_OPS.read_text(encoding="utf-8"))
    assert "issue #766" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "PossibilitiesOS.Remove(ref_type)" not in block


def test_issue766_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #766"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "DeleteType" in body
