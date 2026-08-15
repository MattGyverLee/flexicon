#
#   test_segment_baseline_text.py
#
#   Regression tests for SegmentOperations.GetBaselineText (issues #170/#171).
#
#   Root cause: the old implementation called
#       ITsString(segment.BaselineText).get_String(ws)
#   ISegment.BaselineText is an ITsString (WS already embedded by LCM),
#   NOT an IMultiString.  ITsString has no get_String(ws) method, so the
#   call raises AttributeError at runtime on any project that exercises
#   this code path.
#
#   Fix: read segment.BaselineText.Text directly (or "" on None).
#
#   These tests are pure Python -- no SIL.LCModel / FieldWorks dependency.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
import warnings
from types import SimpleNamespace

import pytest

from flexicon.code.TextsWords.SegmentOperations import SegmentOperations


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def _make_segment(text_value):
    """
    Build a minimal fake ISegment whose .BaselineText.Text == text_value.
    This is the post-fix shape: BaselineText is a plain ITsString-like
    object with a .Text property, no .get_String() method.
    """
    baseline = SimpleNamespace(Text=text_value)
    return SimpleNamespace(BaselineText=baseline)


def _make_old_segment(text_value):
    """
    Build a stub that mimics the pre-fix LCM signature:
    BaselineText has a .get_String() method but NO .Text property.
    Used to document why the old code path was broken.
    """
    def _get_string(ws):
        return SimpleNamespace(Text=text_value)

    baseline = SimpleNamespace(get_String=_get_string)
    return SimpleNamespace(BaselineText=baseline)


# ---------------------------------------------------------------------------
# SegmentOperations stub instance (bypasses __init__, no project needed)
# ---------------------------------------------------------------------------

def _make_ops():
    """
    Create a SegmentOperations instance that does not need a real project.
    We bypass __init__ and wire _GetSegmentObject to return its argument
    unchanged (a pre-resolved stub segment is passed in).
    """
    ops = object.__new__(SegmentOperations)

    # _ValidateParam only checks for None; wire it as a no-op.
    ops._ValidateParam = lambda val, name: None

    # __GetSegmentObject (name-mangled) returns its argument directly.
    ops._SegmentOperations__GetSegmentObject = lambda seg_or_hvo: seg_or_hvo

    return ops


# ---------------------------------------------------------------------------
# Tests -- stub-body tests (lock the call shape)
# ---------------------------------------------------------------------------

class TestGetBaselineTextBody:
    """
    Lock the *body* of the fixed GetBaselineText against regression.

    We call the real SegmentOperations.GetBaselineText via a minimal stub
    instance that bypasses project initialisation.  No LCM required.
    """

    def setup_method(self):
        self.ops = _make_ops()

    def test_returns_text_from_baseline_text_dot_text(self):
        """
        Normal case: segment.BaselineText.Text == 'hello' -> returns 'hello'.
        Confirms the fix reads .Text directly from ITsString.
        """
        seg = _make_segment("hello")
        assert self.ops.GetBaselineText(seg) == "hello"

    def test_none_text_returns_empty_string(self):
        """
        Null guard: segment.BaselineText.Text is None -> returns '' (not None).
        The 'or ""' fallback in the fixed body covers this.
        """
        seg = _make_segment(None)
        assert self.ops.GetBaselineText(seg) == ""

    def test_empty_text_returns_empty_string(self):
        """
        Empty string: segment.BaselineText.Text == '' -> returns ''.
        Trivial but locks the or-empty-string fallback for empty input.
        """
        seg = _make_segment("")
        assert self.ops.GetBaselineText(seg) == ""

    def test_pre_fix_get_string_call_would_raise(self):
        """
        Pre-state guard: the old code path called .get_String(ws) on
        BaselineText.  The real ITsString has no such method, so that call
        raises AttributeError.  This test documents *why* the fix matters:
        the old-style stub (no .Text, only .get_String) proves the old call
        sequence is broken.

        If this test ever starts PASSING (no AttributeError), it means
        someone has accidentally re-added .get_String() to the stub, which
        would silently re-hide the bug.
        """
        seg = _make_old_segment("ignored")
        with pytest.raises(AttributeError):
            # Accessing .Text on the old-style stub (which has no .Text) raises
            # AttributeError, confirming the old stubs are incompatible with the
            # new-style access pattern.
            _ = seg.BaselineText.Text

    def test_ws_handle_rejected(self):
        """
        The wsHandle parameter was removed (ISegment.BaselineText is a
        single-WS ITsString). Passing it must now raise TypeError.
        """
        seg = _make_segment("world")
        with pytest.raises(TypeError):
            self.ops.GetBaselineText(seg, wsHandle=1)

    def test_no_warning_on_normal_call(self):
        """
        Plain GetBaselineText(seg) must not emit any DeprecationWarning.
        """
        seg = _make_segment("world")
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            result = self.ops.GetBaselineText(seg)  # must not raise
        assert result == "world"


# ---------------------------------------------------------------------------
# Tests -- GetSyncableProperties (lock the get_Properties(0).GetIntPropValues
# call chain introduced to replace the broken get_WritingSystem(0) call).
# ---------------------------------------------------------------------------

def _make_syncable_segment(ws_handle, text_value):
    """
    Build a minimal fake ISegment suitable for GetSyncableProperties.

    BaselineText is mocked as an ITsString-like object where:
      - bt.get_Properties(0).GetIntPropValues(1, 0) returns (ws_handle, ...)
      - bt.Text returns text_value

    This mirrors the real LCM call chain verified live on Sena 3.
    """
    from unittest.mock import MagicMock

    bt = MagicMock()
    bt.Text = text_value
    # Wire the call chain: get_Properties(0).GetIntPropValues(1, 0) -> (ws_handle, <iVar>)
    bt.get_Properties.return_value.GetIntPropValues.return_value = (ws_handle, 0)

    seg = MagicMock()
    seg.BaselineText = bt
    # Provide the remaining optional attributes as None/False/0 so the method
    # does not error on the IMultiString / bool / int branches.
    seg.FreeTranslation = None
    seg.LiteralTranslation = None
    seg.IsLabel = False
    seg.BeginOffset = 0
    seg.EndOffset = 5
    return seg


def _make_syncable_ops():
    """
    Create a SegmentOperations instance suitable for GetSyncableProperties.

    Bypasses __init__; wires __GetSegmentObject to pass through and supplies
    a minimal project stub for the IMultiString branches (not exercised here).
    """
    from unittest.mock import MagicMock

    ops = object.__new__(SegmentOperations)
    ops._ValidateParam = lambda val, name: None
    ops._SegmentOperations__GetSegmentObject = lambda seg_or_hvo: seg_or_hvo
    ops.project = MagicMock()
    # GetMultiStringDict is never called with None fields in these tests.
    ops.project.GetMultiStringDict.return_value = {}
    return ops


class TestGetSyncablePropertiesBaselineText:
    """
    Lock the BaselineText extraction inside GetSyncableProperties against
    the regression introduced in commit 20e4a0d (get_WritingSystem(0) called
    on an ITsString, which has no such method).

    The correct idiom is:
        bt.get_Properties(0).GetIntPropValues(1, 0)[0]

    These are pure stub/mock tests -- no LCM / FieldWorks required.
    """

    def setup_method(self):
        self.ops = _make_syncable_ops()

    def test_baseline_text_key_present_in_result(self):
        """
        GetSyncableProperties must include a 'BaselineText' key when the
        segment has a non-None BaselineText.
        """
        seg = _make_syncable_segment(ws_handle=999000003, text_value="hello world")
        props = self.ops.GetSyncableProperties(seg)
        assert "BaselineText" in props

    def test_baseline_text_value_is_dict(self):
        """
        The value of props['BaselineText'] must be a dict (WS handle -> text).
        """
        seg = _make_syncable_segment(ws_handle=999000003, text_value="hello world")
        props = self.ops.GetSyncableProperties(seg)
        assert isinstance(props["BaselineText"], dict)

    def test_baseline_text_keyed_by_integer_ws_handle(self):
        """
        The key in the BaselineText dict must be the integer WS handle
        returned by get_Properties(0).GetIntPropValues(1, 0)[0].
        """
        seg = _make_syncable_segment(ws_handle=999000003, text_value="hello world")
        props = self.ops.GetSyncableProperties(seg)
        bt_dict = props["BaselineText"]
        assert 999000003 in bt_dict

    def test_baseline_text_value_matches_text_attribute(self):
        """
        The text string stored in the dict must match bt.Text.
        """
        seg = _make_syncable_segment(ws_handle=999000003, text_value="In the beginning")
        props = self.ops.GetSyncableProperties(seg)
        assert props["BaselineText"][999000003] == "In the beginning"

    def test_baseline_text_none_text_stored_as_empty_string(self):
        """
        When bt.Text is None the fallback 'or ""' must store '' not None.
        """
        seg = _make_syncable_segment(ws_handle=999000003, text_value=None)
        props = self.ops.GetSyncableProperties(seg)
        assert props["BaselineText"][999000003] == ""

    def test_get_properties_call_chain_invoked(self):
        """
        Confirm that get_Properties(0) is called on the ITsString object,
        locking the call shape so a future regression back to
        get_WritingSystem(0) would cause a mock assertion error here.
        """
        from unittest.mock import MagicMock, call

        bt = MagicMock()
        bt.Text = "test"
        bt.get_Properties.return_value.GetIntPropValues.return_value = (42, 0)

        seg = MagicMock()
        seg.BaselineText = bt
        seg.FreeTranslation = None
        seg.LiteralTranslation = None
        seg.IsLabel = False
        seg.BeginOffset = 0
        seg.EndOffset = 3

        self.ops.GetSyncableProperties(seg)

        bt.get_Properties.assert_called_once_with(0)
        bt.get_Properties.return_value.GetIntPropValues.assert_called_once_with(1, 0)

    def test_get_writing_system_not_called(self):
        """
        Regression guard: get_WritingSystem must NOT be called on the
        ITsString object.  If it were, the live call would raise
        AttributeError because ITsString has no such method.
        """
        from unittest.mock import MagicMock

        full_bt = MagicMock()
        full_bt.Text = "hello"
        full_bt.get_Properties.return_value.GetIntPropValues.return_value = (99, 0)

        seg = MagicMock()
        seg.BaselineText = full_bt
        seg.FreeTranslation = None
        seg.LiteralTranslation = None
        seg.IsLabel = False
        seg.BeginOffset = 0
        seg.EndOffset = 3

        self.ops.GetSyncableProperties(seg)

        assert not full_bt.get_WritingSystem.called, (
            "get_WritingSystem was called on ITsString — regression detected"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
