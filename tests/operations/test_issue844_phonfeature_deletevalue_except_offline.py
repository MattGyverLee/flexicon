#
#   test_issue844_phonfeature_deletevalue_except_offline.py
#
#   Offline ratchet for issue #844 DeleteValue error-path control flow.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PHON_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "PhonFeatureOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue844_phonfeature_deletevalue_except_live.py"
)


def _delete_value_block(text: str) -> str:
    start = text.index("def DeleteValue(self, value_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    # =====", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue844_delete_value_does_not_swallow_parameter_error():
    block = _delete_value_block(PHON_OPS.read_text(encoding="utf-8"))
    assert "issue #844" in block
    assert "except Exception:" not in block
    assert "Value is not a member of ValuesOC" in block
    assert "raise FP_ParameterError" in block


def test_issue844_delete_value_still_uses_hvo_membership():
    block = _delete_value_block(PHON_OPS.read_text(encoding="utf-8"))
    assert "issue #816" in block
    assert "int(slot.Hvo) == target_hvo" in block


def test_issue844_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #844"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "DeleteValue" in body
