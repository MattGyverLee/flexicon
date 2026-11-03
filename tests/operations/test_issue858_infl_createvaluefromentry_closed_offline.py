#
#   test_issue858_infl_createvaluefromentry_closed_offline.py
#
#   Offline ratchet for issue #858 _CreateValueFromEntry IFsClosedFeature guard.
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
    / "test_issue858_infl_createvaluefromentry_closed_live.py"
)


def _create_value_from_entry_block(text: str) -> str:
    start = text.index("def _CreateValueFromEntry(")
    next_def = text.find("\n    # ", start + 1)
    if next_def == -1:
        next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue858_create_value_from_entry_cast_guard_present():
    block = _create_value_from_entry_block(INFL_OPS.read_text(encoding="utf-8"))
    assert "issue #858" in block
    assert "except (AttributeError, System.InvalidCastException):" in block
    assert "_CreateValueFromEntry requires an IFsClosedFeature parent" in block
    guard_pos = block.index("issue #858")
    factory_pos = block.index("IFsSymFeatValFactory")
    assert guard_pos < factory_pos


def test_issue858_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #858"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "_CreateValueFromEntry" in body
