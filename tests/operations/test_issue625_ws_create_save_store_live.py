#
#   test_issue625_ws_create_save_store_live.py
#
#   Class: TestCreateEnsureReachDiskLive
#          Live verification for #625: WritingSystems.Ensure / Create write
#          WritingSystemStore/<tag>.ldml and the idchangelog.xml <Add> entry
#          immediately -- read from disk WITHOUT closing the project and
#          without an explicit store flush.
#
#   Project: target_sandbox (tempdir copy of the Target .fwbackup).
#   Tags qaa-x-t625a / qaa-x-t625b are reserved for this file.
#
#   Invocation (never bare `pytest`):
#     $env:FLEXLIBS_REQUIRE_LIVE = "1"
#     python -m pytest tests/operations/test_issue625_ws_create_save_store_live.py \
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


def _store_dir(project):
    return os.path.join(project.project.ProjectId.ProjectFolder, "WritingSystemStore")


def _changes(project, tag):
    root = ET.parse(os.path.join(_store_dir(project), "idchangelog.xml")).getroot()
    return [(el.tag, el.get("Producer"), el.get("ProducerVersion"))
            for el in root.find("Changes") if el.findtext("Id") == tag]


class TestCreateEnsureReachDiskLive:
    @pytest.mark.live_phase("WritingSystemOperations", "add")
    def test_ensure_writes_ldml_and_add_entry_without_close(self, target_sandbox):
        project, tag = target_sandbox, "qaa-x-t625a"
        ldml = os.path.join(_store_dir(project), tag + ".ldml")
        assert not os.path.exists(ldml)
        assert _changes(project, tag) == []

        ws, created = project.WritingSystems.Ensure(tag, "TEST_t625a")

        assert created is True
        assert project.WritingSystems.Exists(tag) is True
        assert os.path.isfile(ldml), "ldml not on disk before close"
        entries = _changes(project, tag)
        assert [e[0] for e in entries] == ["Add"], entries
        assert entries[0][1] == "flexicon"
        assert entries[0][2] == flexicon.version

    @pytest.mark.live_phase("WritingSystemOperations", "add")
    def test_create_analysis_writes_ldml_and_add_entry_without_close(self, target_sandbox):
        project, tag = target_sandbox, "qaa-x-t625b"
        ldml = os.path.join(_store_dir(project), tag + ".ldml")
        assert not os.path.exists(ldml)

        project.WritingSystems.Create(tag, "TEST_t625b", is_vernacular=False)

        assert tag in project.lp.CurAnalysisWss.split()
        assert os.path.isfile(ldml), "ldml not on disk before close"
        assert [e[0] for e in _changes(project, tag)] == ["Add"]

    @pytest.mark.live_phase("WritingSystemOperations", "add")
    def test_ensure_already_active_adds_no_second_entry(self, target_sandbox):
        project, tag = target_sandbox, "qaa-x-t625a"
        project.WritingSystems.Ensure(tag, "TEST_t625a")
        before = _changes(project, tag)
        ws, created = project.WritingSystems.Ensure(tag, "TEST_t625a")
        assert created is False
        assert _changes(project, tag) == before


class _HostDonor:
    """Duck-typed host project over a live cache (see
    test_attached_view_abort_live.py)."""

    def __init__(self, live_project):
        self.project = live_project.project
        self.lp = live_project.lp
        self.lexDB = live_project.lexDB
        self.writeEnabled = live_project.writeEnabled


class TestSaveInsideAnOuterUnitOfWorkLive:
    """The store save is safe (and happens) when Create/Ensure runs inside a
    caller's unit of work, an undoable operation, or an attached view."""

    @pytest.mark.live_phase("WritingSystemOperations", "add")
    def test_ensure_inside_outer_transaction_legacy_mode(self, target_sandbox):
        project, tag = target_sandbox, "qaa-x-t625c"
        ldml = os.path.join(_store_dir(project), tag + ".ldml")
        with project.Transaction("outer 625"):
            assert project.project.ActionHandlerAccessor.CurrentDepth >= 1
            project.WritingSystems.Ensure(tag, "TEST_t625c")
            assert os.path.isfile(ldml)
        assert [e[0] for e in _changes(project, tag)] == ["Add"]
        assert project.WritingSystems.Exists(tag) is True

    @pytest.mark.live_phase("WritingSystemOperations", "add")
    def test_ensure_inside_outer_undoable_operation(self, target_sandbox_undoable):
        project, tag = target_sandbox_undoable, "qaa-x-t625d"
        ldml = os.path.join(_store_dir(project), tag + ".ldml")
        with project.UndoableOperation("outer 625"):
            assert project.project.ActionHandlerAccessor.CurrentDepth >= 1
            project.WritingSystems.Ensure(tag, "TEST_t625d")
            mid_ldml = os.path.isfile(ldml)
        # Whatever happened mid-UoW, the project must be consistent and the
        # change on disk after the block.
        assert os.path.isfile(ldml)
        assert [e[0] for e in _changes(project, tag)] == ["Add"], mid_ldml
        assert project.WritingSystems.Exists(tag) is True
        assert project.project.ActionHandlerAccessor.CurrentDepth == 0
        # Project still writable afterwards.
        project.WritingSystems.Ensure("qaa-x-t625e", "TEST_t625e")
        assert os.path.isfile(os.path.join(_store_dir(project), "qaa-x-t625e.ldml"))

    @pytest.mark.live_phase("WritingSystemOperations", "add")
    def test_ensure_on_attached_view(self, target_sandbox):
        host, tag = target_sandbox, "qaa-x-t625f"
        view = flexicon.FLExProject.FromOpenProject(_HostDonor(host))
        ldml = os.path.join(_store_dir(host), tag + ".ldml")
        ws, created = view.WritingSystems.Ensure(tag, "TEST_t625f")
        assert created is True
        assert os.path.isfile(ldml)
        assert [e[0] for e in _changes(host, tag)] == ["Add"]
        assert host.project.ActionHandlerAccessor.CurrentDepth == 1
        assert tag in host.lp.CurVernWss.split()
