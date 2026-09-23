#
#   test_issue330_setdateofevent_live.py
#
#   Class: TestIssue330SetDateOfEventLive, TestIssue330SetDateOfBirthLive
#          Live verification for issue #330: IRnGenericRec.DateOfEvent is
#          CLR-typed GenDate, so SetDateOfEvent must reach the LCM for both
#          a System.DateTime and a date string. Assertions read the GenDate
#          components back from a record re-queried by GUID, not the value
#          passed in.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def _reread_gendate(project, record):
    from SIL.LCModel import IRnGenericRec

    return IRnGenericRec(project.Object(record.Guid)).DateOfEvent


class TestIssue330SetDateOfEventLive:
    @pytest.mark.live_phase("DataNotebookOperations", "modify")
    def test_set_date_of_event_from_string(self, target_sandbox):
        ops = target_sandbox.DataNotebook
        rec = ops.Create("TEST_330 string date")
        try:
            ops.SetDateOfEvent(rec, "2024-06-01")
            gd = _reread_gendate(target_sandbox, rec)
            assert (gd.Year, gd.Month, gd.Day) == (2024, 6, 1)
            assert not gd.IsEmpty
        finally:
            ops.Delete(rec)

    @pytest.mark.live_phase("DataNotebookOperations", "modify")
    def test_set_date_of_event_from_datetime(self, target_sandbox):
        from System import DateTime

        ops = target_sandbox.DataNotebook
        rec = ops.Create("TEST_330 DateTime date")
        try:
            ops.SetDateOfEvent(rec, DateTime(2023, 11, 20, 9, 15, 0))
            gd = _reread_gendate(target_sandbox, rec)
            assert (gd.Year, gd.Month, gd.Day) == (2023, 11, 20)
            assert not gd.IsEmpty
        finally:
            ops.Delete(rec)

    @pytest.mark.live_phase("DataNotebookOperations", "modify")
    def test_overwrite_changes_stored_value(self, target_sandbox):
        ops = target_sandbox.DataNotebook
        rec = ops.Create("TEST_330 overwrite")
        try:
            ops.SetDateOfEvent(rec, "2020-01-02")
            ops.SetDateOfEvent(rec, "2021-03-04")
            gd = _reread_gendate(target_sandbox, rec)
            assert (gd.Year, gd.Month, gd.Day) == (2021, 3, 4)
            assert ops.GetDateOfEvent(rec) is not None
        finally:
            ops.Delete(rec)


class TestIssue330SetDateOfBirthLive:
    """Sibling of #330: ICmPerson.DateOfBirth is also GenDate."""

    @pytest.mark.live_phase("PersonOperations", "modify")
    def test_set_and_clear_date_of_birth(self, target_sandbox):
        from SIL.LCModel import ICmPerson

        ops = target_sandbox.Person
        person = ops.Create("TEST_330 person")
        try:
            ops.SetDateOfBirth(person, "1985-03-15")
            gd = ICmPerson(target_sandbox.Object(person.Guid)).DateOfBirth
            assert (gd.Year, gd.Month, gd.Day) == (1985, 3, 15)
            assert not gd.IsEmpty

            ops.SetDateOfBirth(person, "")
            gd = ICmPerson(target_sandbox.Object(person.Guid)).DateOfBirth
            assert gd.IsEmpty
        finally:
            ops.Delete(person)
