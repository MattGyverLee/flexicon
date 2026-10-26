#
#   test_issue704_morphrule_reorder_hvo_offline.py
#
#   Offline ratchet for issue #704 ReorderAffixTemplates HVO membership partition.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
RULE_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "MorphRuleOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue704_morphrule_reorder_hvo_live.py"
)


def _reorder_block(text: str) -> str:
    start = text.index("def ReorderAffixTemplates(self, pos_or_hvo, ordered_templates):")
    next_def = text.find("\n    # ========== DELETION ==========", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue704_reorder_partitions_by_hvo():
    block = _reorder_block(RULE_OPS.read_text(encoding="utf-8"))
    assert "issue #704" in block
    assert "template_by_hvo" in block
    assert "desired = [self.__ResolveObject(t) for t in ordered_templates]" not in block


def test_issue704_reorder_builds_desired_order_from_sequence_members():
    block = _reorder_block(RULE_OPS.read_text(encoding="utf-8"))
    assert "desired_order = [template_by_hvo[hvo]" in block


def test_issue704_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #704"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "ReorderAffixTemplates" in body
