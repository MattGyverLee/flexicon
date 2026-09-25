#
#   test_issue490_phonfeature_resolver_cast_offline.py
#
#   Offline ratchet for issue #490 PhonFeatureOperations HVO resolver cast.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PHON_FEAT_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Grammar" / "PhonFeatureOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue490_phonfeature_resolver_cast_live.py"
)


def test_issue490_resolver_uses_cast_to_concrete():
    text = PHON_FEAT_OPS.read_text(encoding="utf-8")
    assert "from ..lcm_casting import cast_to_concrete" in text
    assert "def __ResolveObject" in text
    idx = text.index("def __ResolveObject")
    body = text[idx : idx + 800]
    assert "return cast_to_concrete(self.project.Object(obj_or_hvo))" in body
    assert "return cast_to_concrete(obj_or_hvo)" in body
    assert "return self.project.Object(obj_or_hvo)" not in body


def test_issue490_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #490"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "GetName" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
