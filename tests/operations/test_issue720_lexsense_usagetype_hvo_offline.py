#
#   test_issue720_lexsense_usagetype_hvo_offline.py
#
#   Offline ratchet for issue #720 LexSense UsageTypesRC HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SENSE_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexSenseOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue720_lexsense_usagetype_hvo_live.py"
)


def _add_usage_type_block(text: str) -> str:
    start = text.index("def AddUsageType(self, sense_or_hvo, usage_type):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_usage_type_block(text: str) -> str:
    start = text.index("def RemoveUsageType(self, sense_or_hvo, usage_type):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue720_add_usage_type_uses_hvo_membership():
    block = _add_usage_type_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #720" in block
    assert "item.Hvo == target_hvo" in block
    assert "usage_type not in sense.UsageTypesRC" not in block
    assert "usage_type in sense.UsageTypesRC" not in block


def test_issue720_remove_usage_type_uses_hvo_membership():
    block = _remove_usage_type_block(SENSE_OPS.read_text(encoding="utf-8"))
    assert "issue #720" in block
    assert "linked.Hvo == target_hvo" in block
    assert "usage_type in sense.UsageTypesRC" not in block


def test_issue720_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #720"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "RemoveUsageType" in body or "AddUsageType" in body
