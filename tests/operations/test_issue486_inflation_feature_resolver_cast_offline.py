#
#   test_issue486_inflation_feature_resolver_cast_offline.py
#
#   Offline ratchet for issue #486 InflectionFeatureOperations HVO resolver casts.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
INFL_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Grammar" / "InflectionFeatureOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue486_inflation_feature_resolver_cast_live.py"
)


def test_issue486_resolvers_use_cast_to_concrete():
    text = INFL_OPS.read_text(encoding="utf-8")
    assert "cast_to_concrete" in text
    assert text.count("cast_to_concrete(self.project.Object") >= 4
    for helper in (
        "__ResolveInflectionClass",
        "__ResolveFeatureStructure",
        "__ResolveFeature",
        "__ResolveFeatureSystem",
    ):
        assert f"def {helper}" in text
    assert "return self.project.Object(ic_or_hvo)" not in text
    assert "return self.project.Object(fs_or_hvo)" not in text
    assert "return self.project.Object(feature_or_hvo)" not in text


def test_issue486_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #486"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "InflectionClassGetName" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
