#
#   test_issue850_infl_createvalue_except_offline.py
#
#   Offline ratchet for issue #850 CreateValue cast guard control flow.
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
    / "test_issue850_infl_createvalue_except_live.py"
)


def _create_value_block(text: str) -> str:
    start = text.index("def CreateValue(self, feature_or_hvo, name, abbreviation")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def DeleteValue", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue850_create_value_cast_guard_is_narrow():
    block = _create_value_block(INFL_OPS.read_text(encoding="utf-8"))
    assert "issue #850" in block
    assert "except (AttributeError, System.InvalidCastException):" in block
    assert "except Exception:" not in block
    assert "CreateValue requires an IFsClosedFeature" in block


def test_issue850_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #850"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "CreateValue" in body
