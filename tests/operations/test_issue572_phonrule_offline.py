#
#   test_issue572_phonrule_offline.py
#
#   Offline coverage for issue #572 (US2): PhonologicalRuleOperations readers.
#   GetSyncableProperties gains a "Disabled" bool key; DescribeRule(None)
#   returns a non-empty str; the seven other new readers raise
#   FP_NullParameterError for None; SetDisabled raises FP_ReadOnlyError when
#   project.writeEnabled is false.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

from types import SimpleNamespace

import pytest

import flexicon.code.Grammar.PhonologicalRuleOperations as phon_rule_ops_module
from flexicon.code.FLExProject import (
    FP_NullParameterError,
    FP_ReadOnlyError,
)
from flexicon.code.Grammar.PhonologicalRuleOperations import (
    PhonologicalRuleOperations,
)

_RULE_GUID = "11111111-2222-3333-4444-555555555555"


class _FakeMultiString:
    """Minimal IMultiString stand-in keyed by writing-system handle."""

    def __init__(self, text_by_handle):
        self._text_by_handle = text_by_handle

    def get_String(self, handle):
        return SimpleNamespace(Text=self._text_by_handle.get(handle, ""))


def _fake_project(write_enabled=True):
    ws = SimpleNamespace(Id="en", Handle=1)
    return SimpleNamespace(
        writeEnabled=write_enabled,
        WritingSystems=SimpleNamespace(GetAll=lambda: [ws]),
    )


def _ops(write_enabled=True):
    return PhonologicalRuleOperations(_fake_project(write_enabled))


def _fake_rule(disabled=True):
    return SimpleNamespace(
        Name=_FakeMultiString({1: "TEST_Rule"}),
        Description=_FakeMultiString({1: "TEST_Desc"}),
        Direction=1,
        StratumRA=SimpleNamespace(Guid=_RULE_GUID),
        Disabled=disabled,
    )


@pytest.fixture
def identity_itsstring(monkeypatch):
    """ITsString as an identity cast so fake multistrings survive GSP."""
    monkeypatch.setattr(phon_rule_ops_module, "ITsString", lambda tss: tss)


class TestGetSyncablePropertiesDisabled:
    def test_gsp_includes_disabled_bool_beside_existing_keys(
        self, identity_itsstring
    ):
        props = _ops().GetSyncableProperties(_fake_rule(disabled=True))
        assert props["Name"] == {"en": "TEST_Rule"}
        assert props["Description"] == {"en": "TEST_Desc"}
        assert props["Direction"] == 1
        assert props["StratumGuid"] == _RULE_GUID
        assert props["Disabled"] is True
        assert isinstance(props["Disabled"], bool)


class TestDescribeRuleNone:
    def test_describe_rule_none_returns_non_empty_str(self):
        result = _ops().DescribeRule(None)
        assert isinstance(result, str)
        assert result != ""


_READERS_RAISING_FOR_NONE = [
    "GetLeftContext",
    "GetRightContext",
    "GetInputPOSes",
    "GetRequiredRuleFeatures",
    "GetExcludedRuleFeatures",
    "IsDisabled",
]


@pytest.mark.parametrize("method_name", _READERS_RAISING_FOR_NONE)
def test_readers_raise_for_none(method_name):
    with pytest.raises(FP_NullParameterError):
        getattr(_ops(), method_name)(None)


def test_set_disabled_none_rule_raises():
    with pytest.raises(FP_NullParameterError):
        _ops().SetDisabled(None, True)


class TestSetDisabledReadOnly:
    def test_set_disabled_valid_rule_read_only(self):
        with pytest.raises(FP_ReadOnlyError):
            _ops(write_enabled=False).SetDisabled(_fake_rule(), True)

    def test_set_disabled_none_rule_read_only_before_null_check(self):
        # _EnsureWriteEnabled fires before _ValidateParam (MorphRule shape).
        with pytest.raises(FP_ReadOnlyError):
            _ops(write_enabled=False).SetDisabled(None, True)
