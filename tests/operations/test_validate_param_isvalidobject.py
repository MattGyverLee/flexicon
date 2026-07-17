#
#   test_validate_param_isvalidobject.py
#
#   Class: TestValidateParamIsValidObject
#          Regression coverage for BaseOperations._ValidateParam's
#          stale-LCM-object guard.
#
#   Bug class (closes #205):
#     A cascade-deleted LCM object keeps a live .NET reference but its
#     internal Cache/Services pointers are torn down, so touching ANY
#     property raises System.NullReferenceException from deep inside LCM
#     (e.g. LcmSet.Remove -> CmObject.DeleteObject). ICmObject exposes
#     IsValidObject, which is False once the object is deleted. Prior to
#     this fix flexlibs2 had zero defensive use of IsValidObject and a
#     stale reference passed into any operation NPE'd opaquely.
#
#     The fix adds a framework-wide guard at the operation entry point
#     (_ValidateParam): if a parameter is an LCM object whose
#     IsValidObject is False, raise FP_ParameterError instead of letting
#     the NPE surface downstream.
#
#   These tests are pure-Python and require neither LCM nor a live FLEx
#   project: the guard is exercised with plain stand-in objects, so it
#   runs in CI where FieldWorks is unavailable.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.BaseOperations import BaseOperations
from flexicon.code.exceptions import (
    FP_NullParameterError,
    FP_ParameterError,
)


class _StubProject:
    """Minimal stand-in; _ValidateParam never touches the project."""

    WriteEnabled = True


class _FakeLcmObject:
    """Stand-in for an LCM object exposing the IsValidObject property."""

    def __init__(self, is_valid):
        self.IsValidObject = is_valid


@pytest.fixture
def ops():
    return BaseOperations(_StubProject())


class TestValidateParamIsValidObject:
    """Locks the #205 stale-reference guard on _ValidateParam."""

    # -- None handling (pre-existing contract, must not regress) --------

    def test_none_raises_null_parameter_error(self, ops):
        with pytest.raises(FP_NullParameterError):
            ops._ValidateParam(None, "item")

    # -- The guard itself -----------------------------------------------

    def test_invalid_lcm_object_raises_parameter_error(self, ops):
        stale = _FakeLcmObject(is_valid=False)
        with pytest.raises(FP_ParameterError) as exc_info:
            ops._ValidateParam(stale, "msa")
        # Message must name the parameter so callers can localize the fault.
        assert "msa" in str(exc_info.value)

    def test_valid_lcm_object_passes(self, ops):
        live = _FakeLcmObject(is_valid=True)
        # Should not raise.
        ops._ValidateParam(live, "msa")

    # -- Non-LCM params must be untouched -------------------------------
    #
    # getattr(param, "IsValidObject", None) returns None for anything
    # that isn't an LCM object, so the guard must skip them. Only an
    # explicit `is False` triggers the error -- never a falsy-but-not-
    # False value.

    @pytest.mark.parametrize(
        "value",
        [
            "some string",
            "",              # empty str is falsy but not an LCM object
            0,               # falsy int
            123,
            0.0,
            {},              # empty dict is falsy
            {"ws": "text"},
            [],              # empty list is falsy
            [1, 2, 3],
            True,
            False,           # bare bool False must NOT be read as invalid
        ],
    )
    def test_non_lcm_params_pass(self, ops, value):
        # Should not raise -- these have no IsValidObject attribute.
        ops._ValidateParam(value, "param")

    def test_object_without_isvalidobject_attr_passes(self, ops):
        class Plain:
            pass

        # No IsValidObject attribute at all -> getattr default None -> skip.
        ops._ValidateParam(Plain(), "param")

    def test_isvalidobject_none_is_not_treated_as_invalid(self, ops):
        # An object whose IsValidObject is explicitly None (not False)
        # must not trip the guard -- only `is False` does.
        obj = _FakeLcmObject(is_valid=None)
        ops._ValidateParam(obj, "param")
