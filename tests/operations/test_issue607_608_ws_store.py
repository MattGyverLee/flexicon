#
#   test_issue607_608_ws_store.py
#
#   Class: TestDeleteUsesLcmDeletion / TestInstallProducerStampIsBestEffort
#          Offline coverage for:
#            - #607: WritingSystemOperations.Delete must use LCM's
#              WritingSystemServices.DeleteWritingSystem and then save the
#              writing-system store (that Save is what moves the .ldml to
#              trash/ and logs the <Delete> entry), instead of only editing
#              the vernacular/analysis lists.
#            - #608: install_producer_stamp() must never raise out of
#              OpenProject, whatever the LCM object looks like.
#
#   The on-disk behaviour itself (ldml in trash/, idchangelog entries,
#   Producer="flexicon") can only be proven live -- see
#   test_issue607_608_ws_store_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from contextlib import contextmanager
from unittest.mock import Mock, patch

import pytest

from flexicon.code.System.WritingSystemOperations import WritingSystemOperations
from flexicon.code.Shared.ws_change_log import install_producer_stamp
from flexicon.code.FLExProject import FP_ParameterError, FP_WritingSystemError

_OPS_MODULE = "flexicon.code.System.WritingSystemOperations"


class _FakeWS:
    def __init__(self, tag, handle):
        self.Id = tag
        self.Handle = handle


def _make_ops(events):
    """Ops bound to a Mock project; `events` records call order."""
    default_vern, default_anal = _FakeWS("etu", 1), _FakeWS("en", 2)
    victim = _FakeWS("qaa-x-victim", 3)

    project = Mock()
    project.writeEnabled = True
    project.project.ServiceLocator.WritingSystems.AllWritingSystems = [
        default_vern, default_anal, victim]
    project.lp.DefaultVernacularWritingSystem = default_vern
    project.lp.DefaultAnalysisWritingSystem = default_anal
    project.project.ServiceLocator.WritingSystemManager.Save.side_effect = (
        lambda: events.append("store_save"))

    ops = WritingSystemOperations(project)

    @contextmanager
    def _tx(label):
        events.append("tx_enter")
        yield
        events.append("tx_exit")

    ops._TransactionCM = _tx
    return ops, project, victim


class TestDeleteUsesLcmDeletion:
    def test_delete_calls_lcm_deletion_then_saves_store_after_transaction(self):
        events = []
        ops, project, victim = _make_ops(events)
        with patch(f"{_OPS_MODULE}.WritingSystemServices") as services:
            services.DeleteWritingSystem.side_effect = (
                lambda cache, ws: events.append("lcm_delete"))
            ops.Delete("qaa-x-victim")

        services.DeleteWritingSystem.assert_called_once_with(
            project.project, victim)
        # The store save must come after the unit of work closes.
        assert events == ["tx_enter", "lcm_delete", "tx_exit", "store_save"]

    def test_delete_by_handle_resolves_same_writing_system(self):
        events = []
        ops, project, victim = _make_ops(events)
        with patch(f"{_OPS_MODULE}.WritingSystemServices") as services:
            ops.Delete(3)
        services.DeleteWritingSystem.assert_called_once_with(
            project.project, victim)

    def test_delete_does_not_hand_edit_lists(self):
        """The list removal is LCM's job now (it also purges data)."""
        events = []
        ops, project, _ = _make_ops(events)
        with patch(f"{_OPS_MODULE}.WritingSystemServices"):
            ops.Delete("qaa-x-victim")
        project.lp.VernacularWritingSystems.Remove.assert_not_called()
        project.lp.CurrentVernacularWritingSystems.Remove.assert_not_called()

    @pytest.mark.parametrize("tag", ["etu", "en"])
    def test_default_writing_systems_refused_without_touching_store(self, tag):
        events = []
        ops, _, _ = _make_ops(events)
        with patch(f"{_OPS_MODULE}.WritingSystemServices") as services:
            with pytest.raises(FP_ParameterError):
                ops.Delete(tag)
        services.DeleteWritingSystem.assert_not_called()
        assert events == []

    def test_unknown_tag_raises(self):
        ops, _, _ = _make_ops([])
        with patch(f"{_OPS_MODULE}.WritingSystemServices") as services:
            with pytest.raises(FP_WritingSystemError):
                ops.Delete("qaa-x-nope")
        services.DeleteWritingSystem.assert_not_called()

    def test_read_only_project_refused(self):
        ops, project, _ = _make_ops([])
        project.writeEnabled = False
        with patch(f"{_OPS_MODULE}.WritingSystemServices") as services:
            with pytest.raises(Exception):
                ops.Delete("qaa-x-victim")
        services.DeleteWritingSystem.assert_not_called()


class TestInstallProducerStampIsBestEffort:
    """OpenProject calls install_producer_stamp unconditionally for
    write-enabled sessions, so it must swallow any LCM shape surprise."""

    def test_returns_false_instead_of_raising_on_hostile_cache(self):
        cache = Mock()
        cache.ServiceLocator.WritingSystemManager.WritingSystemStore.GetType \
            .side_effect = RuntimeError("boom")
        assert install_producer_stamp(cache, "flexicon", "0") is False

    def test_returns_false_when_attribute_chain_missing(self):
        assert install_producer_stamp(object(), "flexicon", "0") is False
