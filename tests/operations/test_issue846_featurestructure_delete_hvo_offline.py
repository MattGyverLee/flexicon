#
#   test_issue846_featurestructure_delete_hvo_offline.py
#
#   Offline ratchet for issue #846 FeatureStructureDelete HVO slot match.
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
    / "test_issue846_featurestructure_delete_hvo_live.py"
)


def _feature_structure_delete_block(text: str) -> str:
    start = text.index("def FeatureStructureDelete(self, fs_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue846_feature_structure_delete_uses_hvo_slot_match():
    block = _feature_structure_delete_block(INFL_OPS.read_text(encoding="utf-8"))
    assert "issue #846" in block
    assert "int(slot_fs.Hvo) == int(fs.Hvo)" in block
    assert "parent.FeaturesOA == fs" not in block


def test_issue846_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #846"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "FeatureStructureDelete" in body
