#
#   test_issue868_infl_featuregetvalues_closed_offline.py
#
#   Offline ratchet for issue #868 FeatureGetValues IFsClosedFeature guard.
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
    / "test_issue868_infl_featuregetvalues_closed_live.py"
)


def _feature_get_values_block(text: str) -> str:
    start = text.index("def FeatureGetValues(self, feature_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def GetFeatures", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue868_feature_get_values_cast_guard_present():
    block = _feature_get_values_block(INFL_OPS.read_text(encoding="utf-8"))
    assert "issue #868" in block
    assert "except (AttributeError, System.InvalidCastException):" in block
    assert "FeatureGetValues requires an IFsClosedFeature" in block
    guard_pos = block.index("issue #868")
    loop_pos = block.index("return list(feature.ValuesOC)")
    assert guard_pos < loop_pos


def test_issue868_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #868"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "FeatureGetValues" in body
