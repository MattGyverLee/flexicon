#
#   test_issue461_phonological_rule_resolver_cast_offline.py
#
#   Offline ratchet for issue #461 PhonologicalRuleOperations HVO resolver cast.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PHON_RULE_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Grammar" / "PhonologicalRuleOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue461_phonological_rule_resolver_cast_live.py"
)


def test_issue461_resolver_uses_cast_to_concrete():
    text = PHON_RULE_OPS.read_text(encoding="utf-8")
    assert "cast_to_concrete" in text
    assert "def __ResolveObject" in text
    assert "return self.project.Object(rule_or_hvo)" not in text
    idx = text.index("def __ResolveObject")
    body = text[idx : idx + 1200]
    assert "return cast_to_concrete(rule_or_hvo)" in body


def test_issue461_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #461"
    gate = LIVE_GATE.read_text(encoding="utf-8")
    assert "GetName" in gate
    assert "isinstance(hvo, int)" in gate
    assert "requires_live_project" in gate
