#
#   test_issue492_possibility_resolver_cast_offline.py
#
#   Offline ratchet for issue #492 PossibilityListOperations HVO resolver casts.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
POSS_OPS = REPO_ROOT / "flexicon" / "code" / "Lists" / "PossibilityListOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue492_possibility_resolver_cast_live.py"
)


def test_issue492_resolvers_use_cast_to_concrete():
    text = POSS_OPS.read_text(encoding="utf-8")
    assert "cast_to_concrete" in text
    assert text.count("cast_to_concrete(self.project.Object") >= 2
    for helper in (
        "__ResolveList",
        "__ResolveItem",
    ):
        assert f"def {helper}" in text
    assert "return self.project.Object(list_or_hvo)" not in text
    assert "return self.project.Object(item_or_hvo)" not in text


def test_issue492_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #492"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "GetItemName" in text
    assert "GetListName" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
