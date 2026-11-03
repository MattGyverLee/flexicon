#
#   test_issue870_phon_applyvalues_closed_offline.py
#
#   Offline ratchet for issue #870 __ApplyValues IFsClosedFeature guard.
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
    / "test_issue870_phon_applyvalues_closed_live.py"
)


def _apply_values_block(text: str) -> str:
    start = text.index("def __ApplyValues(self, item, values, ws_map, fill_gaps):")
    next_def = text.find("\n    def __CreateValueWithGuid", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue870_apply_values_cast_guard_present():
    block = _apply_values_block(PHON_OPS.read_text(encoding="utf-8"))
    assert "issue #870" in block
    assert "except (AttributeError, System.InvalidCastException):" in block
    assert "except Exception:" not in block
    assert "__ApplyValues requires an IFsClosedFeature" in block
    guard_pos = block.index("issue #870")
    loop_pos = block.index("for v in feature.ValuesOC")
    assert guard_pos < loop_pos


def test_issue870_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #870"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "ApplySyncableProperties" in body
