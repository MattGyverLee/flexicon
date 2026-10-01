#
#   test_peer_schema_guard.py
#
#   Offline coverage for the peer schema guard (FLExProject.SetPeerSchemaGuard,
#   capability "peer-schema-guard").
#
#   From a shared-mode peer -- FieldWorks holds the project, this session
#   attached through the shared commit log -- writing-system changes crash the
#   FieldWorks that holds the project. FlexToolsMCP refuses such scripts up
#   front, but an idempotent Ensure() pre-pass is usually a no-op, and refusing
#   it would force users to close FieldWorks for nothing. With the guard on:
#     - Ensure() on an already-active tag still returns (ws, False);
#     - Ensure() that would create or activate raises
#       FP_ExclusiveAccessRequiredError BEFORE any LCM write;
#     - every other writing-system mutator raises before its write.
#   With the guard off (the default) nothing changes.
#
#   Fakes are self-contained, following this suite's convention; the store and
#   active sets are deliberately separate collections (see
#   test_issue250_defects123_ws_activation.py for why).
#
#   Copyright 2026
#

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import flexicon
from flexicon import FP_ExclusiveAccessRequiredError, FP_RuntimeError
from flexicon.code.FLExProject import FLExProject
from flexicon.code.System.WritingSystemOperations import WritingSystemOperations


class _FakeWS:
    def __init__(self, tag, handle):
        self.Id = tag
        self.Handle = handle
        self.Abbreviation = None
        self.DisplayLabel = None
        self.DefaultFontName = "Charis SIL"
        self.DefaultFontSize = 12.0
        self.RightToLeftScript = False


@contextmanager
def _no_transaction(label):
    yield


def _make_ops(all_ws, cur_vern_wss="", cur_analysis_wss="", guard=True):
    mock_project = Mock()
    mock_project.writeEnabled = True
    mock_project._peer_schema_guard = guard
    mock_project.project.ServiceLocator.WritingSystems.AllWritingSystems = all_ws
    mock_project.lp.CurVernWss = cur_vern_wss
    mock_project.lp.CurAnalysisWss = cur_analysis_wss
    mock_project.lp.DefaultVernacularWritingSystem = SimpleNamespace(Handle=-1)
    mock_project.lp.DefaultAnalysisWritingSystem = SimpleNamespace(Handle=-2)

    manager = mock_project.project.ServiceLocator.WritingSystemManager
    manager.Create.side_effect = lambda tag: _FakeWS(tag, 1000)

    ops = WritingSystemOperations(mock_project)
    ops._TransactionCM = _no_transaction
    return ops, mock_project


def _assert_nothing_written(mock_project):
    manager = mock_project.project.ServiceLocator.WritingSystemManager
    assert not manager.Create.called
    assert not manager.Set.called
    assert not mock_project.lp.AddToCurrentVernacularWritingSystems.called
    assert not mock_project.lp.AddToCurrentAnalysisWritingSystems.called


class TestEnsureUnderGuard:
    def test_already_active_is_a_noop_and_does_not_raise(self):
        en = _FakeWS("en", 1)
        ops, proj = _make_ops([en], cur_analysis_wss="en")

        ws, created = ops.Ensure("en", "English", is_vernacular=False)

        assert ws is en
        assert created is False
        _assert_nothing_written(proj)

    def test_absent_tag_raises_before_creating(self):
        ops, proj = _make_ops([_FakeWS("en", 1)], cur_analysis_wss="en")

        with pytest.raises(FP_ExclusiveAccessRequiredError) as exc:
            ops.Ensure("qaa-x-new", "New")

        assert "WritingSystems.Ensure('qaa-x-new')" in str(exc.value)
        assert exc.value.operation == "WritingSystems.Ensure('qaa-x-new')"
        _assert_nothing_written(proj)

    def test_store_present_but_inactive_raises_before_activating(self):
        ops, proj = _make_ops([_FakeWS("en", 1), _FakeWS("fr", 2)], cur_analysis_wss="en")

        with pytest.raises(FP_ExclusiveAccessRequiredError):
            ops.Ensure("fr", "French", is_vernacular=False)

        _assert_nothing_written(proj)

    def test_active_in_other_category_is_a_write_and_raises(self):
        """`en` is analysis-only; ensuring it as vernacular ADDS it there."""
        ops, proj = _make_ops([_FakeWS("en", 1)], cur_analysis_wss="en")

        with pytest.raises(FP_ExclusiveAccessRequiredError):
            ops.Ensure("en", "English")  # is_vernacular defaults to True

        _assert_nothing_written(proj)

    def test_guard_off_creates_as_before(self):
        ops, proj = _make_ops([_FakeWS("en", 1)], cur_analysis_wss="en", guard=False)

        ws, created = ops.Ensure("qaa-x-new", "New")

        assert created is True
        assert ws.Id == "qaa-x-new"
        assert proj.project.ServiceLocator.WritingSystemManager.Set.called
        assert proj.lp.AddToCurrentVernacularWritingSystems.called


class TestOtherMutatorsUnderGuard:
    def test_create_raises_before_writing(self):
        ops, proj = _make_ops([_FakeWS("en", 1)], cur_analysis_wss="en")

        with pytest.raises(FP_ExclusiveAccessRequiredError):
            ops.Create("qaa-x-new", "New")

        _assert_nothing_written(proj)

    def test_delete_raises_before_writing(self):
        fr = _FakeWS("fr", 2)
        ops, proj = _make_ops([_FakeWS("en", 1), fr], cur_analysis_wss="en fr")

        with pytest.raises(FP_ExclusiveAccessRequiredError):
            ops.Delete("fr")

        assert not proj.lp.AnalysisWritingSystems.Remove.called
        assert not proj.lp.CurrentAnalysisWritingSystems.Remove.called

    @pytest.mark.parametrize(
        "call,attr,before",
        [
            (lambda ops, ws: ops.SetFontName(ws, "Doulos SIL"), "DefaultFontName", "Charis SIL"),
            (lambda ops, ws: ops.SetFontSize(ws, 20), "DefaultFontSize", 12.0),
            (lambda ops, ws: ops.SetRightToLeft(ws, True), "RightToLeftScript", False),
        ],
        ids=["SetFontName", "SetFontSize", "SetRightToLeft"],
    )
    def test_setters_raise_before_writing(self, call, attr, before):
        en = _FakeWS("en", 1)
        ops, _ = _make_ops([en], cur_analysis_wss="en")

        with pytest.raises(FP_ExclusiveAccessRequiredError):
            call(ops, en)

        assert getattr(en, attr) == before

    def test_set_default_analysis_raises_before_writing(self):
        pt = _FakeWS("pt", 3)
        ops, proj = _make_ops([_FakeWS("en", 1), pt], cur_analysis_wss="en pt")
        before = proj.lp.DefaultAnalysisWritingSystem

        with pytest.raises(FP_ExclusiveAccessRequiredError):
            ops.SetDefaultAnalysis(pt)

        assert proj.lp.DefaultAnalysisWritingSystem is before

    def test_set_default_vernacular_raises_before_writing(self):
        seh = _FakeWS("seh", 4)
        ops, proj = _make_ops([seh], cur_vern_wss="seh")
        before = proj.lp.DefaultVernacularWritingSystem

        with pytest.raises(FP_ExclusiveAccessRequiredError):
            ops.SetDefaultVernacular(seh)

        assert proj.lp.DefaultVernacularWritingSystem is before


class TestGuardSwitch:
    def test_mock_attribute_is_not_mistaken_for_guard_on(self):
        """A bare Mock project answers `_peer_schema_guard` with a truthy Mock;
        only a real True may switch the guard on."""
        ops = WritingSystemOperations(Mock(writeEnabled=True))
        ops._EnsureSchemaWriteAllowed("WritingSystems.Create('x')")  # no raise

    def test_setter_and_property(self):
        p = FLExProject.__new__(FLExProject)  # no OpenProject needed
        assert p.PeerSchemaGuard is False
        p.SetPeerSchemaGuard(True)
        assert p.PeerSchemaGuard is True
        p.SetPeerSchemaGuard(False)
        assert p.PeerSchemaGuard is False

    def test_capability_and_export(self):
        assert "peer-schema-guard" in flexicon.CAPABILITIES
        assert issubclass(FP_ExclusiveAccessRequiredError, FP_RuntimeError)
        assert "FP_ExclusiveAccessRequiredError" in flexicon.__all__
