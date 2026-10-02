#
#   test_issue626_fromopenproject_producer_live.py
#
#   Live verification for #626: a write-enabled project attached through
#   FLExProject.FromOpenProject (the FlexTools-host path) logs new writing
#   systems in WritingSystemStore/idchangelog.xml as Producer="flexicon".
#
#   The sandbox project plays the host: its cache is handed over through a
#   duck-typed donor (as flexlibs hands FlexTools modules). OpenProject
#   installs the stamp for flexicon-owned sessions, so the test first puts
#   the stock libpalaso mapper back, making the pre-state the unstamped one a
#   foreign host produces. Everything is read back from disk / the LCM.
#
#   Tag qaa-x-test626 is reserved for this file.
#
#   Invocation (never bare `pytest`):
#     $env:FLEXLIBS_REQUIRE_LIVE = "1"
#     python -m pytest tests/operations/test_issue626_fromopenproject_producer_live.py \
#         -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import xml.etree.ElementTree as ET

import pytest

import flexicon
from flexicon.code.FLExProject import FLExProject

pytestmark = pytest.mark.requires_live_project

TAG = "qaa-x-test626"
OWN = "Flexicon.Interop.ProducerStampingMapper"


class _HostDonor:
    """Duck-typed host project (flexlibs shape) over a live cache."""

    def __init__(self, live):
        self.project = live.project
        self.lp = live.lp
        self.lexDB = live.lexDB
        self.writeEnabled = live.writeEnabled


def _change_log(cache):
    from System.Reflection import BindingFlags
    flags = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public
    store = cache.ServiceLocator.WritingSystemManager.WritingSystemStore
    t, field = store.GetType(), None
    while t is not None and field is None:
        field = t.GetField("_changeLog", flags)
        t = t.BaseType
    log = field.GetValue(store)
    return log, log.GetType().GetField("_dataMapper", flags)


def _mapper_type(cache):
    log, mf = _change_log(cache)
    return mf.GetValue(log).GetType().FullName


def _unstamp(cache):
    """Put the stock libpalaso mapper back (a host that never stamped)."""
    log, mf = _change_log(cache)
    cur = mf.GetValue(log)
    if cur.GetType().FullName == OWN:
        mf.SetValue(log, cur._inner)


def _changes(cache):
    path = os.path.join(cache.ProjectId.ProjectFolder,
                        "WritingSystemStore", "idchangelog.xml")
    return [(el.tag, el.get("Producer"), el.get("ProducerVersion"),
             el.findtext("Id"))
            for el in ET.parse(path).getroot().find("Changes")]


class TestFromOpenProjectStampsProducerLive:
    @pytest.mark.live_phase("FLExProject", "add")
    def test_attached_write_enabled_view_logs_flexicon_producer(
            self, target_sandbox):
        host_cache = target_sandbox.project
        _unstamp(host_cache)
        pre_mapper = _mapper_type(host_cache)
        assert pre_mapper.startswith("SIL.WritingSystems."), pre_mapper
        assert [c for c in _changes(host_cache) if c[3] == TAG] == []

        view = FLExProject.FromOpenProject(_HostDonor(target_sandbox))
        assert _mapper_type(host_cache) == OWN

        ws, created = view.WritingSystems.Ensure(TAG, "TEST_test626")
        assert created is True
        host_cache.ServiceLocator.WritingSystemManager.Save()

        post = [c for c in _changes(host_cache) if c[3] == TAG]
        assert len(post) == 1, post
        kind, producer, version, _ = post[0]
        assert kind == "Add"
        assert producer == "flexicon"
        assert version == flexicon.version

    @pytest.mark.live_phase("FLExProject", "read")
    def test_read_only_donor_is_not_stamped(self, target_sandbox):
        host_cache = target_sandbox.project
        _unstamp(host_cache)
        donor = _HostDonor(target_sandbox)
        donor.writeEnabled = False
        FLExProject.FromOpenProject(donor)
        assert _mapper_type(host_cache).startswith("SIL.WritingSystems.")
