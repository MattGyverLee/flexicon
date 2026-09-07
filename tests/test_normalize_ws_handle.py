#
#   test_normalize_ws_handle.py
#
#   Regression tests for `normalize_ws_handle()` in
#   flexicon.code.Shared.string_utils.
#
#   Fix: issues #170/#171 -- GetBaselineText called .get_String(ws) on an
#   ITsString (single-WS) instead of reading .Text directly.  The ws
#   argument was obtained via FLExProject.__WSHandle, which now routes
#   through normalize_ws_handle() so object-typed WS args don't blow up
#   with a pythonnet TypeError before even reaching LCM.
#
#   Pure Python -- no SIL.LCModel / FieldWorks dependency.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
import pytest

from flexicon.code.Shared.string_utils import normalize_ws_handle


# ---------------------------------------------------------------------------
# Minimal stub: an object that looks like CoreWritingSystemDefinition
# ---------------------------------------------------------------------------
class _WS:
    Handle = 42


class _WSNoHandle:
    """Object with no .Handle attribute at all."""
    pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNormalizeWsHandle:
    """
    Coverage for normalize_ws_handle() -- the helper that smooths over
    int vs CoreWritingSystemDefinition writing-system arguments.

    All tests are pure-Python; no live LCM required.
    """

    def test_none_returns_none(self):
        """None is the sentinel for 'use default WS'; must pass through."""
        assert normalize_ws_handle(None) is None

    def test_zero_int_returns_zero(self):
        """
        Zero is a valid (if unusual) int handle -- edge case for falsy int.
        The function must NOT treat 0 as None or a missing value.
        """
        result = normalize_ws_handle(0)
        assert result == 0
        assert isinstance(result, int)

    def test_positive_int_passthrough(self):
        """Ordinary int handle is returned unchanged."""
        assert normalize_ws_handle(42) == 42

    def test_object_with_handle_attribute(self):
        """
        CoreWritingSystemDefinition-like object: .Handle is extracted
        and returned as int.
        """
        ws_obj = _WS()
        assert normalize_ws_handle(ws_obj) == 42

    def test_string_raises_type_error(self):
        """
        A string such as 'en' is NOT a valid ws argument here -- strings
        are looked up upstream by FLExProject.WSHandle before this helper
        is called.  Passing a raw string must raise TypeError, not silently
        succeed or crash pythonnet further down.
        """
        with pytest.raises(TypeError):
            normalize_ws_handle("en")

    def test_plain_object_without_handle_raises_type_error(self):
        """
        An arbitrary object with no .Handle attribute has no safe
        interpretation and must raise TypeError.
        """
        with pytest.raises(TypeError):
            normalize_ws_handle(_WSNoHandle())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
