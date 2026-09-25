#
#   test_issue506_findbyhvo_resolver_offline.py
#
#   Offline ratchet for issue #506 FindByHvo HVO resolution.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CONST_CHART = REPO_ROOT / "flexicon" / "code" / "Discourse" / "ConstChartOperations.py"
REVERSAL_ENTRY = (
    REPO_ROOT / "flexicon" / "code" / "Reversal" / "ReversalIndexEntryOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue506_findbyhvo_resolver_live.py"
)


def _findbyhvo_block(text: str) -> str:
    start = text.index("def FindByHvo")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue506_const_chart_findbyhvo_routes_through_resolve_object():
    block = _findbyhvo_block(CONST_CHART.read_text(encoding="utf-8"))
    assert "return self.__ResolveObject(hvo)" in block
    assert "isinstance(obj, IDsConstChart)" not in block


def test_issue506_reversal_entry_findbyhvo_routes_through_resolve_object():
    block = _findbyhvo_block(REVERSAL_ENTRY.read_text(encoding="utf-8"))
    assert "return self.__ResolveObject(hvo)" in block
    assert "isinstance(obj, IReversalIndexEntry)" not in block


def test_issue506_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #506"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "FindByHvo" in text
    assert "requires_live_project" in text
