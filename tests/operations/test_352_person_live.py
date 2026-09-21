#
#   test_352_person_live.py
#
#   Live regression coverage for issue #352 (Person face):
#   ICmPerson.Gender is Int32 (not a string); Email/PlaceOfBirth/Comment
#   do not exist; notes live in the inherited NotesOA StText.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


class Test352PersonGenderInt:
    @pytest.mark.live_phase("PersonOperations", "add")
    def test_gender_roundtrip(self, target_sandbox):
        op = target_sandbox.Person
        person = op.Create("TEST_352 gender")
        try:
            assert op.GetGender(person) == 0
            op.SetGender(person, 1)
            assert op.GetGender(person) == 1
        finally:
            op.Delete(person)

    @pytest.mark.live_phase("PersonOperations", "read")
    def test_set_gender_rejects_string(self, target_sandbox):
        op = target_sandbox.Person
        person = op.Create("TEST_352 gender str")
        try:
            with pytest.raises(FP_ParameterError):
                op.SetGender(person, "Male")
        finally:
            op.Delete(person)


class Test352PersonRetiredFields:
    @pytest.mark.live_phase("PersonOperations", "read")
    def test_email_phone_notes_raise_actionable(self, target_sandbox):
        op = target_sandbox.Person
        person = op.Create("TEST_352 retired")
        try:
            for call in (
                lambda: op.GetEmail(person),
                lambda: op.SetEmail(person, "a@b.c"),
                lambda: op.GetPhone(person),
                lambda: op.SetPhone(person, "123"),
                lambda: op.GetNotes(person),
                lambda: op.AddNote(person, "x"),
            ):
                with pytest.raises(FP_ParameterError, match="352"):
                    call()
        finally:
            op.Delete(person)


class Test352PersonDuplicateSync:
    @pytest.mark.live_phase("PersonOperations", "add")
    def test_duplicate_conserves_int_gender(self, target_sandbox):
        op = target_sandbox.Person
        person = op.Create("TEST_352 dup")
        try:
            op.SetGender(person, 2)
            dup = op.Duplicate(person)
            try:
                assert op.GetGender(dup) == 2
                props = op.GetSyncableProperties(dup)
                assert props["Gender"] == 2
                assert "Email" not in props
                assert props["PlaceOfBirthRA"] is None
                is_diff, _ = op.CompareTo(person, dup)
                assert not is_diff
            finally:
                op.Delete(dup)
        finally:
            op.Delete(person)
