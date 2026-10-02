#
#   test_issue626_fromopenproject_producer.py
#
#   Offline coverage for #626: FLExProject.FromOpenProject installs the
#   same best-effort Producer="flexicon" change-log stamp as OpenProject
#   (#608) for a write-enabled donor, never raises, and never overrides a
#   change-log mapper the host installed.
#
#   The on-disk effect is proven live -- see
#   tests/operations/test_issue626_fromopenproject_producer_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import logging
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from flexicon.code.FLExProject import FLExProject
from flexicon.code.Shared import ws_change_log
from flexicon.code.Shared.ws_change_log import (
    install_flexicon_producer_stamp,
    install_producer_stamp,
)
from tests.test_from_open_project import _FakeDonor

_HELPER = "flexicon.code.Shared.ws_change_log.install_flexicon_producer_stamp"


class TestFromOpenProjectInstallsStamp:
    def test_write_enabled_donor_gets_stamp_on_its_cache(self):
        donor = _FakeDonor(write_enabled=True)
        with patch(_HELPER) as helper:
            FLExProject.FromOpenProject(donor)
        helper.assert_called_once_with(donor.project, quiet=True)

    def test_read_only_donor_is_left_alone(self):
        with patch(_HELPER) as helper:
            FLExProject.FromOpenProject(_FakeDonor(write_enabled=False))
        helper.assert_not_called()

    def test_flexicon_donor_is_returned_unchanged_without_stamping(self):
        existing = FLExProject.FromOpenProject(_FakeDonor(write_enabled=True))
        with patch(_HELPER) as helper:
            assert FLExProject.FromOpenProject(existing) is existing
        helper.assert_not_called()

    def test_stamp_failure_never_breaks_attach(self):
        donor = _FakeDonor(write_enabled=True)
        with patch(_HELPER, side_effect=RuntimeError("boom")):
            view = FLExProject.FromOpenProject(donor)
        assert view.project is donor.project
        assert view.writeEnabled is True

    def test_fake_cache_without_store_attaches_cleanly(self):
        """No patching: the real helper meets a cache with no WS store."""
        view = FLExProject.FromOpenProject(_FakeDonor(write_enabled=True))
        assert view.writeEnabled is True


def _cache_with_mapper(full_name):
    """Mock LcmCache whose change log holds a mapper of the given type."""
    mapper = Mock()
    mapper.GetType.return_value.FullName = full_name
    mapper_field = Mock()
    mapper_field.GetValue.return_value = mapper
    change_log = Mock()
    change_log.GetType.return_value.GetField.return_value = mapper_field
    log_field = Mock()
    log_field.GetValue.return_value = change_log

    store = Mock()
    store.GetType.return_value.GetField.return_value = log_field
    cache = Mock()
    cache.ServiceLocator.WritingSystemManager.WritingSystemStore = store
    return cache, mapper_field


@pytest.fixture
def fake_clr(monkeypatch):
    """Stand-in for System.Reflection and the mapper class (no CLR)."""
    monkeypatch.setitem(sys.modules, "System", MagicMock())
    monkeypatch.setitem(sys.modules, "System.Reflection", MagicMock())
    monkeypatch.setattr(
        ws_change_log, "_build_mapper_class",
        lambda: (lambda inner, p, v: ("STAMPING", inner, p, v)))


class TestHostMapperIsNotOverridden:
    def test_host_installed_mapper_is_left_alone(self, fake_clr):
        cache, mapper_field = _cache_with_mapper("FlexTools.MyMapper")
        assert install_producer_stamp(cache, "flexicon", "1") is False
        mapper_field.SetValue.assert_not_called()

    def test_stock_palaso_mapper_is_wrapped(self, fake_clr):
        cache, mapper_field = _cache_with_mapper(
            "SIL.WritingSystems.WritingSystemChangeLogDataMapper")
        assert install_producer_stamp(cache, "flexicon", "1") is True
        mapper_field.SetValue.assert_called_once()
        assert mapper_field.SetValue.call_args[0][1][0] == "STAMPING"

    def test_already_installed_is_idempotent(self, fake_clr):
        cache, mapper_field = _cache_with_mapper(
            "Flexicon.Interop.ProducerStampingMapper")
        assert install_producer_stamp(cache, "flexicon", "1") is True
        mapper_field.SetValue.assert_not_called()


class TestSharedHelperNeverRaises:
    def test_hostile_cache_returns_false(self):
        assert install_flexicon_producer_stamp(object(), quiet=True) is False

    def test_quiet_logs_debug_not_warning(self, caplog):
        with caplog.at_level(logging.DEBUG, logger=ws_change_log.logger.name):
            install_producer_stamp(object(), "flexicon", "0", quiet=True)
        assert caplog.records
        assert all(r.levelno == logging.DEBUG for r in caplog.records)
