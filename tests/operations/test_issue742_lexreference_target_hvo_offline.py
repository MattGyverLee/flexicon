#
#   test_issue742_lexreference_target_hvo_offline.py
#
#   Offline ratchet for issue #742 LexReferenceOperations TargetsRS HVO membership.
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
    / "test_issue742_lexreference_target_hvo_live.py"
)


def _method_block(text: str, method_name: str) -> str:
    start = text.index(f"def {method_name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue742_remove_target_uses_hvo_membership():
    source = LEXREF_OPS.read_text(encoding="utf-8")
    block = _method_block(source, "RemoveTarget")
    assert "issue #742" in block
    assert "linked.Hvo == target_hvo" in block
    assert "target in lex_ref.TargetsRS" not in block
    assert "Remove(target)" not in block


def test_issue742_remove_target_scans_targets_rs():
    source = LEXREF_OPS.read_text(encoding="utf-8")
    block = _method_block(source, "RemoveTarget")
    assert "for linked in lex_ref.TargetsRS" in block


def test_issue742_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #742"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemoveTarget" in body
