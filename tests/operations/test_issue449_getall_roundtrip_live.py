#
#   test_issue449_getall_roundtrip_live.py
#
#   Live gate for issue #449: GetAll() wrapper items round-trip through
#   Operations read methods without pythonnet cast failures.
#
#   Copyright 2026
#

import sys

import pytest


pytestmark = pytest.mark.requires_live_project


def _open_sena3_readonly():
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception:
        return None
    project = FLExProject()
    try:
        project.OpenProject("Sena 3", writeEnabled=False)
        return project
    except Exception:
        return None


@pytest.fixture(scope="module")
def sena3_project():
    if "SIL.LCModel" not in sys.modules:
        pytest.importorskip("SIL.LCModel")
    project = _open_sena3_readonly()
    if project is None:
        pytest.skip("Sena 3 not available for live #449 gate")
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


class TestIssue449GetAllRoundTrip:
    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_getform_accepts_getall_wrappers(self, sena3_project):
        project = sena3_project
        checked = 0
        for entry in project.lexDB.Entries:
            if not entry.LexemeFormOA:
                continue
            for item in project.Allomorphs.GetAll(entry):
                form = project.Allomorphs.GetForm(item)
                assert form is not None or form == ""
                checked += 1
            if checked >= 25:
                break
        assert checked > 0, "expected at least one allomorph wrapper to exercise"

    @pytest.mark.live_phase("MSAOperations", "read")
    def test_get_syncable_properties_accepts_msa_getall_wrappers(self, sena3_project):
        project = sena3_project
        checked = 0
        for entry in project.lexDB.Entries:
            for msa in project.MSA.GetAll(entry):
                props = project.MSA.GetSyncableProperties(msa)
                assert isinstance(props, dict)
                checked += 1
                if checked >= 25:
                    return
        assert checked > 0, "expected at least one MSA wrapper to exercise"
