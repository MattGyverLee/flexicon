#
#   test_issue502_wfigloss_analysis_resolver_cast_offline.py
#
#   Offline ratchet for issue #502 WfiGlossOperations analysis HVO resolver cast.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WFI_GLOSS_OPS = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "WfiGlossOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue502_wfigloss_analysis_resolver_cast_live.py"
)


def test_issue502_shared_resolver_and_no_inline_isinstance_hvo_guards():
    text = WFI_GLOSS_OPS.read_text(encoding="utf-8")
    assert "from ..lcm_casting import cast_to_concrete" in text
    assert "def __ResolveAnalysis" in text
    assert text.count("self.__ResolveAnalysis(") >= 5
    assert 'if not isinstance(analysis, IWfiAnalysis)' not in text
    assert "cast_to_concrete(obj)" in text
    assert 'ClassName", None) == "WfiAnalysis"' in text


def test_issue502_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #502"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "GetCount" in body
    assert "isinstance(hvo, int)" in body
    assert "requires_live_project" in body
