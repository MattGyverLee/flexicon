#
#   test_issue625_ws_create_save_store.py
#
#   Class: TestCreateEnsureSaveStore
#          Offline coverage for #625: WritingSystems.Create / Ensure save the
#          writing-system store right after adding the writing system (as
#          Delete does), Ensure stays a no-op when the tag is already
#          active, and the peer schema guard fires before any write.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from contextlib import contextmanager
from unittest.mock import Mock

import pytest

from flexicon.code.System.WritingSystemOperations import WritingSystemOperations
from flexicon.code.FLExProject import FP_ParameterError, FP_WritingSystemError


class _FakeWS:
    def __init__(self, tag, handle=9):
        self.Id = tag
        self.Handle = handle


def _make_ops(events, store_tags=()):
    default_vern, default_anal = _FakeWS("etu", 1), _FakeWS("en", 2)
    stored = [default_vern, default_anal] + [_FakeWS(t) for t in store_tags]

    project = Mock()
    project.writeEnabled = True
    project.project.ServiceLocator.WritingSystems.AllWritingSystems = stored
    project.lp.DefaultVernacularWritingSystem = default_vern
    project.lp.DefaultAnalysisWritingSystem = default_anal
    project.lp.CurVernWss = "etu"
    project.lp.CurAnalysisWss = "en"
    project.lp.VernacularWritingSystems = [default_vern]
    project.lp.AnalysisWritingSystems = [default_anal]
    mgr = project.project.ServiceLocator.WritingSystemManager
    mgr.Create.side_effect = lambda tag: _FakeWS(tag)
    mgr.Set.side_effect = lambda ws: events.append("set")
    mgr.Save.side_effect = lambda: events.append("store_save")
    project.lp.AddToCurrentVernacularWritingSystems.side_effect = (
        lambda ws: events.append("activate"))
    project.lp.AddToCurrentAnalysisWritingSystems.side_effect = (
        lambda ws: events.append("activate"))

    ops = WritingSystemOperations(project)

    @contextmanager
    def _tx(label):
        events.append("tx_enter")
        yield
        events.append("tx_exit")

    ops._TransactionCM = _tx
    return ops, project


class TestCreateEnsureSaveStore:
    def test_create_saves_store_after_transaction(self):
        events = []
        ops, _ = _make_ops(events)
        ws = ops.Create("qaa-x-new", "New")
        assert ws.Id == "qaa-x-new"
        assert events == ["tx_enter", "set", "activate", "tx_exit", "store_save"]

    def test_create_analysis_saves_store(self):
        events = []
        ops, _ = _make_ops(events)
        ops.Create("qaa-x-new", "New", is_vernacular=False)
        assert events[-1] == "store_save"

    def test_ensure_new_saves_store_after_transaction(self):
        events = []
        ops, _ = _make_ops(events)
        ws, created = ops.Ensure("qaa-x-new", "New")
        assert created is True and ws.Id == "qaa-x-new"
        assert events == ["tx_enter", "set", "activate", "tx_exit", "store_save"]

    def test_ensure_store_present_inactive_activates_and_saves(self):
        events = []
        ops, _ = _make_ops(events, store_tags=["qaa-x-old"])
        ws, created = ops.Ensure("qaa-x-old", "Old")
        assert created is False
        assert events == ["tx_enter", "activate", "tx_exit", "store_save"]

    def test_ensure_already_active_is_noop_without_save(self):
        events = []
        ops, _ = _make_ops(events)
        ws, created = ops.Ensure("etu", "Whatever")
        assert created is False
        assert events == []

    def test_create_already_active_raises_without_save(self):
        events = []
        ops, _ = _make_ops(events)
        with pytest.raises(FP_ParameterError):
            ops.Create("etu", "Dup")
        assert events == []

    @pytest.mark.parametrize("call", ["Create", "Ensure"])
    def test_schema_guard_refuses_before_any_write(self, call):
        events = []
        ops, _ = _make_ops(events)
        ops._EnsureSchemaWriteAllowed = Mock(side_effect=RuntimeError("guard"))
        with pytest.raises(RuntimeError, match="guard"):
            getattr(ops, call)("qaa-x-new", "New")
        assert events == []

    def test_store_save_failure_raises_clear_error_after_lcm_change(self):
        events = []
        ops, project = _make_ops(events)
        project.project.ServiceLocator.WritingSystemManager.Save.side_effect = (
            OSError("disk full"))
        with pytest.raises(FP_WritingSystemError, match="disk full"):
            ops.Ensure("qaa-x-new", "New")
        assert "activate" in events  # LCM change was already made
