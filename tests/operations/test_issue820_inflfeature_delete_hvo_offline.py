#
#   test_issue820_inflfeature_delete_hvo_offline.py
#
#   Offline ratchet for issue #820 InflectionFeatureOperations FeatureDelete HVO lookup.
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
    / "test_issue820_inflfeature_delete_hvo_live.py"
)


def _feature_delete_block(text: str) -> str:
    start = text.index("def FeatureDelete(self, feature_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue820_feature_delete_uses_hvo_membership():
    block = _feature_delete_block(INFL_OPS.read_text(encoding="utf-8"))
    assert "issue #820" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "FeaturesOC.Remove(feature)" not in block


def test_issue820_feature_delete_raises_when_not_member():
    block = _feature_delete_block(INFL_OPS.read_text(encoding="utf-8"))
    assert "Feature is not a member of FeaturesOC" in block


def test_issue820_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #820"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "FeatureDelete" in body
