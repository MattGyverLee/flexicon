#
#   test_issue488_phoneme_code_resolver_cast_offline.py
#
#   Offline ratchet for issue #488 PhonemeOperations code HVO resolver cast.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PHONEME_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "PhonemeOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue488_phoneme_code_resolver_cast_live.py"
)


def test_issue488_code_resolver_uses_cast_to_concrete():
    text = PHONEME_OPS.read_text(encoding="utf-8")
    assert "from ..lcm_casting import cast_to_concrete" in text
    assert "def __GetCodeObject" in text
    assert "return cast_to_concrete(self.project.Object(code_or_hvo))" in text
    assert "return cast_to_concrete(code_or_hvo)" in text
    assert "return self.project.Object(code_or_hvo)" not in text


def test_issue488_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #488"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "RemoveCode" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
