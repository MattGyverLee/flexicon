#
#   test_issue640_getbeststring_offline.py
#
#   Offline ratchet for issue #640 GetBestString multistring validation.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WS_OPS = REPO_ROOT / "flexicon" / "code" / "System" / "WritingSystemOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue640_getbeststring_live.py"
)


def _get_best_string_block(text: str) -> str:
    start = text.index("def GetBestString")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue640_get_best_string_uses_is_instance_of_type():
    block = _get_best_string_block(WS_OPS.read_text(encoding="utf-8"))
    assert "issue #640" in block
    assert "clr.GetClrType(IMultiUnicode).IsInstanceOfType" in block
    assert "clr.GetClrType(IMultiString).IsInstanceOfType" in block
    assert "isinstance(string_obj" not in block
    assert "best_text(string_obj)" in block


def test_issue640_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #640"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetBestString" in body


# --- Behavioural tests (stub objects exercise both branches) -----------------


class _FakeClrType:
    """Stands in for a System.Type: IsInstanceOfType keyed on a marker."""

    def __init__(self, marker):
        self._marker = marker

    def IsInstanceOfType(self, obj):
        return getattr(obj, "_clr_kind", None) == self._marker


def _make_ops(monkeypatch):
    import clr
    from SIL.LCModel import IMultiString, IMultiUnicode

    from flexicon.code.System.WritingSystemOperations import WritingSystemOperations
    from flexicon.code.Shared import string_utils

    def fake_get_clr_type(iface):
        if iface is IMultiUnicode:
            return _FakeClrType("multiunicode")
        if iface is IMultiString:
            return _FakeClrType("multistring")
        return _FakeClrType(None)

    monkeypatch.setattr(clr, "GetClrType", fake_get_clr_type)
    seen = []
    monkeypatch.setattr(
        string_utils, "best_text", lambda obj: (seen.append(obj), "BEST")[1]
    )
    ops = object.__new__(WritingSystemOperations)
    return ops, seen


class _Stub:
    def __init__(self, kind):
        self._clr_kind = kind


def test_issue640_get_best_string_accepts_multiunicode(monkeypatch):
    ops, seen = _make_ops(monkeypatch)
    obj = _Stub("multiunicode")
    assert ops.GetBestString(obj) == "BEST"
    assert seen == [obj]


def test_issue640_get_best_string_accepts_multistring(monkeypatch):
    ops, seen = _make_ops(monkeypatch)
    obj = _Stub("multistring")
    assert ops.GetBestString(obj) == "BEST"
    assert seen == [obj]


def test_issue640_get_best_string_rejects_other_types(monkeypatch):
    import pytest
    from flexicon.code.FLExProject import FP_ParameterError

    ops, seen = _make_ops(monkeypatch)
    with pytest.raises(FP_ParameterError):
        ops.GetBestString(_Stub("something_else"))
    with pytest.raises(FP_ParameterError):
        ops.GetBestString("plain python str")
    assert seen == []
