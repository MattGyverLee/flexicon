#
#   test_issue748_phonrule_delete_hvo_offline.py
#
#   Offline ratchet for issue #748 Delete / DeleteConstraint HVO membership.
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
    / "test_issue748_phonrule_delete_hvo_live.py"
)


def _delete_block(text: str) -> str:
    start = text.index("def Delete(self, rule_or_hvo)")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _delete_constraint_block(text: str) -> str:
    start = text.index("def DeleteConstraint(self, constraint_or_hvo)")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue748_delete_uses_hvo_membership():
    block = _delete_block(PHON_RULE_OPS.read_text(encoding="utf-8"))
    assert "issue #748" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "rule in phon_data.PhonRulesOS" not in block


def test_issue748_delete_constraint_uses_hvo_membership():
    block = _delete_constraint_block(PHON_RULE_OPS.read_text(encoding="utf-8"))
    assert "issue #748" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "constraint not in phon_data.FeatConstraintsOS" not in block


def test_issue748_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #748"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
