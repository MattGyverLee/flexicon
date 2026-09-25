#
#   test_issue500_wordform_resolver_cast_offline.py
#
#   Offline ratchet for issue #500 WordformOperations HVO resolver cast.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORDFORM_OPS = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "WordformOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue500_wordform_resolver_cast_live.py"
)


def test_issue500_shared_resolver_and_no_inline_isinstance_hvo_guards():
    text = WORDFORM_OPS.read_text(encoding="utf-8")
    assert "from ..lcm_casting import cast_to_concrete" in text
    assert "def __ResolveWordform" in text
    assert text.count("self.__ResolveWordform(") >= 10
    assert 'if not isinstance(wordform, IWfiWordform)' not in text
    assert "cast_to_concrete(obj)" in text
    assert 'ClassName", None) == "WfiWordform"' in text


def test_issue500_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #500"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "GetForm" in body
    assert "isinstance(hvo, int)" in body
    assert "requires_live_project" in body
