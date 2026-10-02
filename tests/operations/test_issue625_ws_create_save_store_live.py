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
