#
#   test_issue319_participants_researchers_live.py
#
#   Class: DataNotebookOperations
#          Live-DB effect coverage for issue #319: GetResearchers/
#          AddResearcher/RemoveResearcher and GetParticipants/
#          AddParticipant/RemoveParticipant against a real FieldWorks
#          project (LCM 11). The mock-based unit tests in
#          test_issue319_participants_researchers.py cover the logic
#          in isolation; this file confirms the real LCM properties
#          (ResearchersRC, ParticipantsOC, DefaultRoledParticipants,
#          MakeDefaultRoledParticipant) behave as the fix assumes.
#
#          Every assertion here re-reads state fresh from the record
#          after the mutating call, rather than trusting a stale
#          in-memory handle -- "returns a list" alone would have passed
#          against the pre-fix broken code, which is why #319 shipped.
#
#          NOTE on unrelated, pre-existing, deeper bugs discovered while
#          writing these tests (see cycle2-programmer-319.md for the full
#          writeup -- NOT fixed here, out of scope for #319):
#
#          1. DataNotebookOperations.Create() calls
#             `repos.RecordsOC.Add(record)` directly on the
#             IRnResearchNbkRepository service object, but the real LCM 11
#             repository has no `RecordsOC` attribute -- the collection
#             lives on `repos.Singleton.RecordsOC` (the singleton
#             IRnResearchNbk container). GetAll()/Find() have the mirror
#             bug: they iterate `repos.AllInstances()`, which yields the
#             singleton IRnResearchNbk container object (Count == 1), not
#             IRnGenericRec records. To keep this file able to build a
#             record for the fixtures below despite that, `temp_record`
#             builds one directly via IRnGenericRecFactory +
#             repos.Singleton.RecordsOC.Add(), bypassing Create()/Find()
#             entirely.
#
#          2. RESOLVED 2026-09-20. `DataNotebookOperations.__GetRecordObject`
#             (the private helper EVERY public method in this class --
#             including all six fixed for #319 -- calls to resolve
#             `record_or_hvo`) used to call `self.project.project.GetObject(hvo)`,
#             but the real LCM 11 `LcmCache` has no `GetObject` method; it
#             lives on `LcmCache.ServiceLocator.GetObject(hvo)`. That raised
#             `FP_ParameterError` for EVERY call into EVERY
#             DataNotebookOperations method against a real LCM 11 database,
#             so the six tests below could not pass anywhere. They were
#             marked `xfail(strict=True)` to make CI announce the moment the
#             helper was fixed.
#
#             It has been: the lcm-member-truth-sweep work for #261/#302
#             routed record resolution through `project.Object` and the
#             owning `RecordsOC`. The strict markers duly XPASSed and have
#             been removed; all six now pass live against "Sena 3".
#
#          The #319 fix itself (the six methods' actual LCM property
#          usage: ResearchersRC, ParticipantsOC, DefaultRoledParticipants,
#          MakeDefaultRoledParticipant) WAS independently verified against
#          this same live "Sena 3" database by calling those exact
#          operations directly on real LCM objects, bypassing the broken
#          helper -- see cycle2-programmer-319.md for that transcript.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# Every test in this module opens a real .fwdata project via writable_project.
pytestmark = pytest.mark.requires_live_project


_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_project(write_enabled):
    """Open the first candidate project that responds. None if none work."""
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception:
        return None

    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=write_enabled)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    """
    Module-scoped, write-enabled real FLExProject. Skipped if SIL.LCModel
    isn't loaded or no candidate project opens.
    """
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")

    project = _try_open_project(write_enabled=True)
    if project is None:
        pytest.skip(
            "No writable FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )

    yield project

    try:
        project.CloseProject()
    except Exception:
        pass


@pytest.fixture
def temp_record(writable_project):
    """
    Create a throwaway IRnGenericRec directly against the LCM repository,
    deliberately bypassing DataNotebook.Create()/Find()/GetAll(). See the
    module docstring above: those three methods have a pre-existing bug
    (unrelated to #319) that makes them non-functional against a real
    LCM 11 database, independent of this fix.
    """
    from SIL.LCModel import IRnResearchNbkRepository, IRnGenericRecFactory

    repos = writable_project.project.ServiceLocator.GetService(
        IRnResearchNbkRepository
    )
    factory = writable_project.project.ServiceLocator.GetService(
        IRnGenericRecFactory
    )
    notebook = repos.Singleton

    with writable_project.UndoableOperation("test: create issue #319 record"):
        record = factory.Create()
        notebook.RecordsOC.Add(record)

    yield record

    try:
        with writable_project.UndoableOperation("test: delete issue #319 record"):
            notebook.RecordsOC.Remove(record)
    except Exception:
        pass


@pytest.fixture
def temp_persons(writable_project):
    """Create two throwaway ICmPerson objects, deleted after the test."""
    names = ("TEST_issue319_person_a", "TEST_issue319_person_b")
    created = []
    for name in names:
        existing = writable_project.Person.Find(name)
        if existing is not None:
            try:
                writable_project.Person.Delete(existing)
            except Exception:
                pass
        created.append(writable_project.Person.Create(name))

    yield created

    for person in created:
        try:
            writable_project.Person.Delete(person)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Researchers -- pure rename, RC-backed
# ---------------------------------------------------------------------------


class TestResearchersLive:
    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_add_researcher_effect_pre_post(self, writable_project, temp_record, temp_persons):
        person_a, _ = temp_persons

        before = writable_project.DataNotebook.GetResearchers(temp_record)
        assert person_a not in before

        writable_project.DataNotebook.AddResearcher(temp_record, person_a)

        after = writable_project.DataNotebook.GetResearchers(temp_record)
        assert person_a in after

    @pytest.mark.live_phase("DataNotebookOperations", "remove")
    def test_remove_researcher_effect_pre_post(self, writable_project, temp_record, temp_persons):
        person_a, _ = temp_persons

        writable_project.DataNotebook.AddResearcher(temp_record, person_a)
        assert person_a in writable_project.DataNotebook.GetResearchers(temp_record)

        writable_project.DataNotebook.RemoveResearcher(temp_record, person_a)

        assert person_a not in writable_project.DataNotebook.GetResearchers(temp_record)


# ---------------------------------------------------------------------------
# Participants -- two-hop navigation via ParticipantsOC / DefaultRoledParticipants
# ---------------------------------------------------------------------------


class TestParticipantsLive:
    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_add_participant_creates_group_when_absent(
        self, writable_project, temp_record, temp_persons
    ):
        """Highest-risk path: record has no roled-partic group yet, so
        AddParticipant must create one via MakeDefaultRoledParticipant()
        and the person must show up afterward."""
        person_a, _ = temp_persons

        count_before = len(list(temp_record.ParticipantsOC))
        assert count_before == 0

        writable_project.DataNotebook.AddParticipant(temp_record, person_a)

        count_after = len(list(temp_record.ParticipantsOC))
        assert count_after == count_before + 1

        participants = writable_project.DataNotebook.GetParticipants(temp_record)
        assert person_a in participants

    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_add_participant_reuses_existing_group(
        self, writable_project, temp_record, temp_persons
    ):
        """A second AddParticipant call must not create a second group."""
        person_a, person_b = temp_persons

        writable_project.DataNotebook.AddParticipant(temp_record, person_a)
        count_after_first = len(list(temp_record.ParticipantsOC))

        writable_project.DataNotebook.AddParticipant(temp_record, person_b)
        count_after_second = len(list(temp_record.ParticipantsOC))

        assert count_after_second == count_after_first

        participants = writable_project.DataNotebook.GetParticipants(temp_record)
        assert person_a in participants
        assert person_b in participants

    @pytest.mark.live_phase("DataNotebookOperations", "remove")
    def test_remove_participant_unlinks_without_destroying_group(
        self, writable_project, temp_record, temp_persons
    ):
        """CRITICAL: RemoveParticipant must unlink the person from the
        group's ParticipantsRC, and must NOT reduce ParticipantsOC's
        count -- that would mean the whole role group (an owned object)
        was destroyed instead of just unlinking a reference."""
        person_a, _ = temp_persons

        writable_project.DataNotebook.AddParticipant(temp_record, person_a)
        assert person_a in writable_project.DataNotebook.GetParticipants(temp_record)

        count_before_remove = len(list(temp_record.ParticipantsOC))

        writable_project.DataNotebook.RemoveParticipant(temp_record, person_a)

        count_after_remove = len(list(temp_record.ParticipantsOC))
        assert count_after_remove == count_before_remove

        assert person_a not in writable_project.DataNotebook.GetParticipants(temp_record)

    @pytest.mark.live_phase("DataNotebookOperations", "remove")
    def test_remove_participant_from_multiple_groups(
        self, writable_project, temp_record, temp_persons
    ):
        """If a person is linked into more than one role group (via direct
        LCM access, since AddParticipant only ever targets the default
        group), RemoveParticipant must strip them from every group."""
        person_a, _ = temp_persons

        # First group: the default, via the public API.
        writable_project.DataNotebook.AddParticipant(temp_record, person_a)

        # Second group: created directly against LCM to simulate a
        # role-specific group the public API cannot create (no `role`
        # parameter on AddParticipant).
        with writable_project.UndoableOperation("test: second role group"):
            second_group = temp_record.MakeDefaultRoledParticipant()
            second_group.ParticipantsRC.Add(person_a)

        assert len(list(temp_record.ParticipantsOC)) == 2

        writable_project.DataNotebook.RemoveParticipant(temp_record, person_a)

        # Both groups remain (never destroyed), but neither still
        # references person_a.
        assert len(list(temp_record.ParticipantsOC)) == 2
        for group in temp_record.ParticipantsOC:
            assert person_a not in list(group.ParticipantsRC)
