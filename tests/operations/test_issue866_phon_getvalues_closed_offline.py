#
#   test_issue866_phon_getvalues_closed_offline.py
#
#   Offline ratchet for issue #866 GetValues IFsClosedFeature guard.
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
    / "test_issue866_phon_getvalues_closed_live.py"
)


def _get_values_block(text: str) -> str:
    start = text.index("def GetValues(self, feature_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def Find", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue866_get_values_cast_guard_present():
    block = _get_values_block(PHON_OPS.read_text(encoding="utf-8"))
    assert "issue #866" in block
    assert "except (AttributeError, System.InvalidCastException):" in block
    assert "GetValues requires an IFsClosedFeature" in block
    guard_pos = block.index("issue #866")
    loop_pos = block.index("for val in feature.ValuesOC")
    assert guard_pos < loop_pos


def test_issue866_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #866"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetValues" in body
