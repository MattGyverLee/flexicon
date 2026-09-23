#
#   test_issue255_affix_slot.py
#
#   Offline coverage for POSOperations.CreateAffixSlot and
#   MorphRuleOperations.AddSlotToTemplate (issue #255).
#
#   Mocks the slot factory, AffixSlotsOC.Add, and the four template
#   reference sequences. No live FieldWorks project is opened.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import contextlib

import pytest

from flexicon.code.FLExProject import (
    FP_NullParameterError,
    FP_ParameterError,
    FP_ReadOnlyError,
)
from flexicon.code.Grammar.MorphRuleOperations import MorphRuleOperations
from flexicon.code.Grammar.POSOperations import POSOperations


class _CallLog:
    def __init__(self):
        self.events = []


class _Name:
    def __init__(self, log):
        self._log = log
        self.writes = []

    def set_String(self, ws, text):
        self._log.events.append("name")
        self.writes.append((ws, text))


class _Slot:
    def __init__(self, log, owner_hvo=1):
        self._log = log
        self.Name = _Name(log)
        self.Owner = _Owner(owner_hvo)
        self.Hvo = 50
        self._optional = None
        self.optional_seen = False

    @property
    def Optional(self):
        return self._optional

    @Optional.setter
    def Optional(self, value):
        self._log.events.append("optional")
        self.optional_seen = True
        self._optional = value


class _Owner:
    def __init__(self, hvo):
        self.Hvo = hvo


class _AffixSlotsOC:
    def __init__(self, log):
        self._log = log
        self.added = []

    def Add(self, item):
        self._log.events.append("add")
        assert "name" not in self._log.events
        assert "optional" not in self._log.events
        self.added.append(item)


class _Pos:
    """Not ClassName PartOfSpeech, so __ResolveObject returns it unchanged."""

    ClassName = None

    def __init__(self, log):
        self.AffixSlotsOC = _AffixSlotsOC(log)
        self.Hvo = 1


class _Sequence:
    def __init__(self, items=None):
        self.items = list(items or [])
        self.add_calls = []
        self.insert_calls = []

    @property
    def Count(self):
        return len(self.items)

    def Add(self, item):
        self.add_calls.append(item)
        self.items.append(item)

    def Insert(self, index, item):
        self.insert_calls.append((index, item))
        self.items.insert(index, item)


class _Template:
    def __init__(self, owner_hvo=1):
        self.Owner = _Owner(owner_hvo)
        self.Hvo = 80
        self.PrefixSlotsRS = _Sequence()
        self.SuffixSlotsRS = _Sequence()
        self.ProcliticSlotsRS = _Sequence()
        self.EncliticSlotsRS = _Sequence()


def _project(write_enabled=True):
    from unittest.mock import Mock

    project = Mock()
    project.writeEnabled = write_enabled
    project.project.DefaultAnalWs = 999
    return project


def _pos_ops(log, write_enabled=True):
    project = _project(write_enabled)
    slot = _Slot(log)
    factory = type("Factory", (), {})()
    factory.Create = lambda: log.events.append("create") or slot
    project.project.ServiceLocator.GetService = lambda factory_type: factory
    ops = POSOperations(project)
    ops._TransactionCM = lambda label: contextlib.nullcontext()
    return ops, project, slot, factory


def _rule_ops(write_enabled=True):
    project = _project(write_enabled)
    ops = MorphRuleOperations(project)
    ops._TransactionCM = lambda label: contextlib.nullcontext()
    return ops


class TestCreateAffixSlotValidation:
    def test_null_pos_and_name_raise(self):
        log = _CallLog()
        ops, _, _, _ = _pos_ops(log)
        pos = _Pos(log)

        with pytest.raises(FP_NullParameterError):
            ops.CreateAffixSlot(None, "PossConcord")
        with pytest.raises(FP_NullParameterError):
            ops.CreateAffixSlot(pos, None)
        assert log.events == []

    @pytest.mark.parametrize("name", ["", "   "])
    def test_blank_name_raises(self, name):
        log = _CallLog()
        ops, _, _, _ = _pos_ops(log)

        with pytest.raises(FP_ParameterError):
            ops.CreateAffixSlot(_Pos(log), name)
        assert "create" not in log.events

    def test_read_only_project_raises(self):
        log = _CallLog()
        ops, _, _, _ = _pos_ops(log, write_enabled=False)

        with pytest.raises(FP_ReadOnlyError):
            ops.CreateAffixSlot(_Pos(log), "PossConcord")
        assert log.events == []


class TestCreateAffixSlotCallOrder:
    def test_name_and_optional_written_only_after_add(self, monkeypatch):
        log = _CallLog()
        ops, project, slot, _factory = _pos_ops(log)
        pos = _Pos(log)
        sentinel = object()

        class _TsStringUtils:
            @staticmethod
            def MakeString(text, ws):
                log.events.append("makestring")
                assert "add" in log.events
                return sentinel

        monkeypatch.setattr(
            "flexicon.code.Grammar.POSOperations.TsStringUtils",
            _TsStringUtils,
        )

        created = ops.CreateAffixSlot(pos, "PossConcord", optional=False)

        assert created is slot
        assert log.events == ["create", "add", "makestring", "name", "optional"]
        assert pos.AffixSlotsOC.added == [slot]
        assert slot.Name.writes == [(project.project.DefaultAnalWs, sentinel)]
        assert slot.Optional is False
        assert slot.optional_seen is True


class TestAddSlotToTemplate:
    def test_bad_side_raises(self):
        ops = _rule_ops()
        template = _Template()
        slot = _Slot(_CallLog())

        with pytest.raises(FP_ParameterError):
            ops.AddSlotToTemplate(template, slot, "infix")
        assert template.PrefixSlotsRS.add_calls == []
        assert template.SuffixSlotsRS.add_calls == []
        assert template.ProcliticSlotsRS.add_calls == []
        assert template.EncliticSlotsRS.add_calls == []

    def test_owner_mismatch_raises(self):
        ops = _rule_ops()
        template = _Template(owner_hvo=1)
        slot = _Slot(_CallLog(), owner_hvo=2)

        with pytest.raises(FP_ParameterError):
            ops.AddSlotToTemplate(template, slot, "prefix")
        assert template.PrefixSlotsRS.add_calls == []
        assert template.PrefixSlotsRS.insert_calls == []

    def test_index_none_appends(self):
        ops = _rule_ops()
        template = _Template(owner_hvo=7)
        slot = _Slot(_CallLog(), owner_hvo=7)
        template.PrefixSlotsRS.items.append(object())

        returned = ops.AddSlotToTemplate(template, slot, "PREFIX")

        assert returned is template
        assert template.PrefixSlotsRS.add_calls == [slot]
        assert template.PrefixSlotsRS.insert_calls == []
        assert template.SuffixSlotsRS.add_calls == []
        assert template.ProcliticSlotsRS.add_calls == []
        assert template.EncliticSlotsRS.add_calls == []

    def test_index_inserts_and_out_of_range_raises(self):
        ops = _rule_ops()
        template = _Template(owner_hvo=7)
        slot = _Slot(_CallLog(), owner_hvo=7)

        with pytest.raises(FP_ParameterError):
            ops.AddSlotToTemplate(template, slot, "suffix", index=1)
        assert template.SuffixSlotsRS.insert_calls == []

        returned = ops.AddSlotToTemplate(template, slot, "suffix", index=0)
        assert returned is template
        assert template.SuffixSlotsRS.insert_calls == [(0, slot)]
        assert template.SuffixSlotsRS.add_calls == []

    def test_read_only_project_raises(self):
        ops = _rule_ops(write_enabled=False)
        template = _Template()
        slot = _Slot(_CallLog())

        with pytest.raises(FP_ReadOnlyError):
            ops.AddSlotToTemplate(template, slot, "prefix")
        assert template.PrefixSlotsRS.add_calls == []
