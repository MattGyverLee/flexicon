#
#   test_issue770_msa_exception_feature_hvo_offline.py
#
#   Offline ratchet for issue #770 exception-feature RC HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MSA_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "MSAOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue770_msa_exception_feature_hvo_live.py"
)


def _method_block(text: str, name: str) -> str:
    needle = f"def {name}"
    start = text.index(needle)
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue770_add_exception_feature_uses_hvo_membership():
    text = MSA_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "AddExceptionFeature")
    assert "issue #770" in block
    assert "int(item.Hvo) == target_hvo" in block
    assert "poss not in rc" not in block


def test_issue770_remove_exception_feature_uses_hvo_membership():
    text = MSA_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "RemoveExceptionFeature")
    assert "issue #770" in block
    assert "member_to_remove" in block
    assert "poss in rc" not in block


def test_issue770_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #770"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemoveExceptionFeature" in body
