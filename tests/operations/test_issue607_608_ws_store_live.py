#
#   test_issue607_608_ws_store_live.py
#
#   Class: TestProducerAttributionLive / TestDeleteReachesStoreLive /
#          TestReadOnlyOpenLive
#          Live verification for:
#            - #608: writing systems created through flexicon are logged in
#              WritingSystemStore/idchangelog.xml as Producer="flexicon",
#              not Producer="???".
#            - #607: WritingSystems.Delete removes the .ldml from the
#              store (moved to trash/), logs a <Delete> entry, and
#              ExistsInStore() turns False.
#
#   Everything is read back FROM DISK (the sandbox's WritingSystemStore) and
#   from the LCM after the write -- never from values passed in.
#
#   Project: target_sandbox / target_sandbox_undoable (tempdir copies of the
#   Target .fwbackup) and a private tempdir copy for the read-only open.
#   Tag qaa-x-testdel is reserved for this file.
#
#   Invocation (never bare `pytest` -- it executes ~322 live tests in place):
#     $env:FLEXLIBS_REQUIRE_LIVE = "1"
#     python -m pytest tests/operations/test_issue607_608_ws_store_live.py \
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

pytestmark = pytest.mark.requires_live_project

TAG = "qaa-x-testdel"


def _store_dir(project):
    return os.path.join(project.project.ProjectId.ProjectFolder, "WritingSystemStore")


def _changes(project):
    """Return [(kind, producer, producer_version, id)] read from disk."""
    path = os.path.join(_store_dir(project), "idchangelog.xml")
    root = ET.parse(path).getroot()
    out = []
    for el in root.find("Changes"):
        out.append((el.tag, el.get("Producer"), el.get("ProducerVersion"),
                    el.findtext("Id")))
    return out


def _flush_store(project):
    """What CloseProject does for the WS store, without closing."""
    project.project.ServiceLocator.WritingSystemManager.Save()


class TestProducerAttributionLive:
    @pytest.mark.live_phase("WritingSystemOperations", "add")
    def test_created_ws_is_logged_with_flexicon_producer(self, target_sandbox):
        project = target_sandbox
        pre = [c for c in _changes(project) if c[3] == TAG]
        assert pre == [], "pre-state: tag must not be logged yet"

        ws, created = project.WritingSystems.Ensure(TAG, "TEST_testdel")
        assert created is True
        _flush_store(project)

        post = [c for c in _changes(project) if c[3] == TAG]
        assert len(post) == 1, post
        kind, producer, version, _ = post[0]
        assert kind == "Add"
        assert producer == "flexicon"
        assert version == flexicon.version
        # FieldWorks' own pre-existing entries are untouched.
        others = [c for c in _changes(project) if c[3] != TAG]
        assert others and all(c[1] != "flexicon" for c in others)

    @pytest.mark.live_phase("WritingSystemOperations", "add")
    def test_producer_survives_close_without_explicit_flush(self, target_sandbox):
        """The entry is attributed when written by CloseProject's own save."""
        project = target_sandbox
        folder = _store_dir(project)
        project.WritingSystems.Ensure(TAG, "TEST_testdel")
        project.CloseProject()

        path = os.path.join(folder, "idchangelog.xml")
        root = ET.parse(path).getroot()
        added = [el for el in root.find("Changes")
                 if el.findtext("Id") == TAG]
        assert len(added) == 1
        assert added[0].get("Producer") == "flexicon"
        assert added[0].get("ProducerVersion") == flexicon.version


class TestDeleteReachesStoreLive:
    @pytest.mark.live_phase("WritingSystemOperations", "delete")
    def test_delete_removes_ldml_logs_delete_and_clears_store(self, target_sandbox):
        self._run(target_sandbox)

    @pytest.mark.live_phase("WritingSystemOperations", "delete")
    def test_delete_in_undoable_mode(self, target_sandbox_undoable):
        self._run(target_sandbox_undoable)

    @staticmethod
    def _run(project):
        ws_ops = project.WritingSystems
        store = _store_dir(project)
        ldml = os.path.join(store, TAG + ".ldml")

        ws_ops.Ensure(TAG, "TEST_testdel")
        _flush_store(project)
        # Pre-state, read back from disk and LCM.
        assert os.path.isfile(ldml)
        assert ws_ops.ExistsInStore(TAG) is True
        assert TAG in project.lp.CurVernWss.split()
        assert [c[0] for c in _changes(project) if c[3] == TAG] == ["Add"]

        ws_ops.Delete(TAG)

        # Post-state, re-queried from the LCM and the disk.
        assert ws_ops.ExistsInStore(TAG) is False
        assert ws_ops.Exists(TAG) is False
        assert TAG not in project.lp.CurVernWss.split()
        assert TAG not in project.lp.CurAnalysisWss.split()
        assert TAG not in [w.Id for w in project.lp.VernacularWritingSystems]
        assert not os.path.exists(ldml), "ldml still in the live store"
        assert os.path.isfile(os.path.join(store, "trash", TAG + ".ldml"))

        entries = [c for c in _changes(project) if c[3] == TAG]
        assert [e[0] for e in entries] == ["Add", "Delete"]
        assert entries[1][1] == "flexicon"
        assert entries[1][2] == flexicon.version

    @pytest.mark.live_phase("WritingSystemOperations", "delete")
    def test_default_ws_still_refused_and_store_untouched(self, target_sandbox):
        project = target_sandbox
        default_tag = project.WritingSystems.GetDefaultVernacular().Id
        before = sorted(os.listdir(_store_dir(project)))
        with pytest.raises(flexicon.FP_ParameterError):
            project.WritingSystems.Delete(default_tag)
        assert sorted(os.listdir(_store_dir(project))) == before
        assert project.WritingSystems.ExistsInStore(default_tag) is True


class TestReadOnlyOpenLive:
    @pytest.mark.live_phase("FLExProject", "read")
    def test_read_only_open_is_unaffected(self):
        """Opening read-only must keep working (no producer hook needed)."""
        from tests.flex_plugin import _FwBackupSandbox
        import pathlib
        from flexicon.code.FLExProject import FLExProject

        backups = sorted(
            (pathlib.Path(__file__).resolve().parent.parent / "fixtures")
            .glob("Target*.fwbackup"))
        assert backups, "Target fixture missing"
        with _FwBackupSandbox(backups[-1], prefix="ro_607_") as fwdata:
            ro = FLExProject()
            ro.OpenProject(str(fwdata), writeEnabled=False)
            try:
                assert ro.writeEnabled is False
                assert list(ro.WritingSystems.GetAll())
                assert ro.WritingSystems.ExistsInStore("en") is True
            finally:
                ro.CloseProject()
