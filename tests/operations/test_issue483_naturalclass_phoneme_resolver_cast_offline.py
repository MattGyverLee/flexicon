#
#   test_issue483_naturalclass_phoneme_resolver_cast_offline.py
#
#   Offline ratchet for issue #483 NaturalClassOperations phoneme resolver cast.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NATURAL_CLASS_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Grammar" / "NaturalClassOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue483_naturalclass_phoneme_resolver_cast_live.py"
)


def test_issue483_phoneme_resolver_uses_cast_to_concrete():
    text = NATURAL_CLASS_OPS.read_text(encoding="utf-8")
    assert "from ..lcm_casting import cast_to_concrete" in text
    assert "def __GetPhonemeObject" in text
    assert "return cast_to_concrete(self.project.Object(phoneme_or_hvo))" in text
    assert "return cast_to_concrete(phoneme_or_hvo)" in text
    assert "return self.project.Object(phoneme_or_hvo)" not in text


def test_issue483_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #483"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "AddPhoneme" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
