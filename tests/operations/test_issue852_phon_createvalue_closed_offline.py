#
#   test_issue852_phon_createvalue_closed_offline.py
#
#   Offline ratchet for issue #852 CreateValue IFsClosedFeature guard.
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
    / "test_issue852_phon_createvalue_closed_live.py"
)


def _create_value_block(text: str) -> str:
    start = text.index("def CreateValue(self, feature_or_hvo, name, abbreviation")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def DeleteValue", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue852_create_value_cast_guard_present():
    block = _create_value_block(PHON_OPS.read_text(encoding="utf-8"))
    assert "issue #852" in block
    assert "except (AttributeError, System.InvalidCastException):" in block
    assert "CreateValue requires an IFsClosedFeature" in block
    # Guard must appear before the ownership-first Add, not the docstring mention.
    guard_pos = block.index("issue #852")
    add_pos = block.index("feature.ValuesOC.Add(new_val)")
    assert guard_pos < add_pos


def test_issue852_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #852"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "CreateValue" in body
