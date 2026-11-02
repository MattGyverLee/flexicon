#
#   test_issue848_infl_deletevalue_hvo_offline.py
#
#   Offline ratchet for issue #848 InflectionFeatureOperations DeleteValue.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
INFL_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "InflectionFeatureOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue848_infl_deletevalue_hvo_live.py"
)


def _delete_value_block(text: str) -> str:
    start = text.index("def DeleteValue(self, value_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue848_delete_value_uses_hvo_membership():
    block = _delete_value_block(INFL_OPS.read_text(encoding="utf-8"))
    assert "issue #848" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "ValuesOC.Remove(val)" not in block


def test_issue848_delete_value_does_not_swallow_parameter_error():
    block = _delete_value_block(INFL_OPS.read_text(encoding="utf-8"))
    assert "except Exception:" not in block
    assert "Value is not a member of ValuesOC" in block
    assert "raise FP_ParameterError" in block


def test_issue848_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #848"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "DeleteValue" in body
