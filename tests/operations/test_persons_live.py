#
#   test_persons_live.py
#
#   Class: PersonOperations
#          Live-DB tests against Sena 3 covering the four applicable
#          phases of the stabilization model:
#              A. read-only
#              B. create + delete in-place (TEST_ prefix, finally cleanup)
#              C. reorder       -- N/A (PeopleOC is unordered)
#              D. modify (capture-restore)
#              E. delete pre-existing (sandbox copy, real target)
#
#          Sena 3 ships with 6 pre-existing CmPerson rows, which makes
#          PersonOperations the first class where Phase E has a real
#          target. The Phase E test snapshots one pre-existing person's
#          name + GUID, deletes the person inside the sena3_sandbox
#          fixture, and confirms the deletion -- never touching the
#          user's real Sena 3.
#
#          Replicates the Cycle-2 template from test_locations_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# Every test in this module opens a real .fwdata project via
# writable_project or sena3_sandbox.
pytestmark = pytest.mark.requires_live_project


# ---------------------------------------------------------------------------
# Live-project fixture (canonical pattern; matches test_phonemes.py /
# test_locations_live.py)
# ---------------------------------------------------------------------------

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
    """Module-scoped, write-enabled real FLExProject."""
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


def _delete_if_present(project, name):
    """Pre-clean a TEST_ person left from a crashed prior run."""
    existing = project.Person.Find(name)
    if existing is not None:
        try:
            project.Person.Delete(existing)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Phase A: read-only
# ---------------------------------------------------------------------------


class TestPersonsPhaseARead:
    """Phase A: getters return without raising."""

    @pytest.mark.live_phase("PersonOperations", "read")
    def test_get_all_returns_iterable(self, writable_project):
        """GetAll() returns an iterable that yields persons (Sena 3 has 6)."""
        people = list(writable_project.Person.GetAll())
        assert isinstance(people, list)
        # Sena 3 ships with 6 persons; other candidate projects may differ.
        # Don't hard-code the count -- just assert it's a list-of-persons.

    @pytest.mark.live_phase("PersonOperations", "read")
    def test_find_returns_none_for_missing(self, writable_project):
        """Find() returns None for an obviously absent name."""
        result = writable_project.Person.Find(
            "TEST_zzqxxx_nonexistent_for_phase_a"
        )
        assert result is None

    @pytest.mark.live_phase("PersonOperations", "read")
    def test_exists_returns_false_for_missing(self, writable_project):
        """Exists() returns False for an obviously absent name."""
        assert (
            writable_project.Person.Exists(
                "TEST_zzqxxx_nonexistent_for_phase_a"
            )
            is False
        )


# ---------------------------------------------------------------------------
# Phase B: create + delete in-place
# ---------------------------------------------------------------------------


class TestPersonsPhaseBAdd:
    """Phase B: create a TEST_ person, verify, delete in finally."""

    @pytest.mark.live_phase("PersonOperations", "add")
    def test_create_and_delete_roundtrip(self, writable_project):
        """Create -> assert name + Exists -> Delete -> assert absent."""
        name = "TEST_person_phase_b_roundtrip"

        _delete_if_present(writable_project, name)

        person = writable_project.Person.Create(name)
        try:
            assert person is not None
            assert writable_project.Person.GetName(person) == name
            assert writable_project.Person.Exists(name) is True
        finally:
            try:
                writable_project.Person.Delete(person)
            except Exception:
                pass

        assert writable_project.Person.Find(name) is None


# ---------------------------------------------------------------------------
# Phase C: reorder (N/A for PersonOperations)
# ---------------------------------------------------------------------------


class TestPersonsPhaseCReorder:
    """
    Phase C is not applicable to PersonOperations.

    Persons are owned by `lp.PeopleOC` -- an LcmOwningCollection,
    which is unordered by definition. There is no IndexOf, no
    MoveTo, no concept of position. The "reorder" phase exists for
    classes whose underlying storage is an Owning Sequence (OS),
    such as LocationOperations.PossibilitiesOS or SensesOS.
    """

    @pytest.mark.live_phase("PersonOperations", "reorder")
    @pytest.mark.skip(
        reason=(
            "N/A: lp.PeopleOC is an unordered collection (OC). "
            "Reorder is only meaningful for ordered sequences (OS)."
        )
    )
    def test_reorder_not_applicable(self, writable_project):
        """Placeholder: see class docstring."""
        ...


# ---------------------------------------------------------------------------
# Phase D: modify + restore
# ---------------------------------------------------------------------------


class TestPersonsPhaseDModify:
    """
    Phase D: capture name, set new value, restore captured.

    Operates on a freshly-created TEST_ person rather than a
    pre-existing Sena 3 person so a mid-test crash leaves no
    residue in the real project. LCM's DateModified churn is
    accepted (scripts/restore_sena3.py wipes it between sessions).
    """

    @pytest.mark.live_phase("PersonOperations", "modify")
    def test_name_capture_modify_restore(self, writable_project):
        """SetName(new) then SetName(captured) round-trips the value."""
        name = "TEST_person_phase_d_modify"
        new_name = "TEST_person_phase_d_modified"

        _delete_if_present(writable_project, name)
        _delete_if_present(writable_project, new_name)

        person = writable_project.Person.Create(name)
        try:
            captured = writable_project.Person.GetName(person)
            assert captured == name

            writable_project.Person.SetName(person, new_name)
            assert writable_project.Person.GetName(person) == new_name

            writable_project.Person.SetName(person, captured)
            assert writable_project.Person.GetName(person) == name
        finally:
            try:
                writable_project.Person.Delete(person)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase E: delete pre-existing person in sandbox (REAL Phase E)
# ---------------------------------------------------------------------------


class TestPersonsPhaseEDelete:
    """
    Phase E: delete a pre-existing person, inside an isolated copy of
    Sena 3. This is the first class in the suite where Phase E has a
    truly destructive target -- Sena 3 ships with 6 CmPerson rows, so
    deletion exercises the cascade-removal path against real project
    data without ever touching the user's real Sena 3.

    The test snapshots one person's name and GUID, deletes the person,
    and confirms Find/Exists report it gone. The sandbox tempdir is
    torn down on fixture exit; the user's real project is untouched.
    """

    @pytest.mark.live_phase("PersonOperations", "delete")
    def test_delete_preexisting_person_in_sandbox(self, sena3_sandbox):
        """Snapshot a pre-existing person, delete it, confirm gone."""
        people = list(sena3_sandbox.Person.GetAll())
        if not people:
            pytest.skip(
                "Sandbox project has no pre-existing persons "
                "(expected 6 in Sena 3); cannot exercise Phase E here."
            )

        # Pick the first person -- any will do, we never persist the
        # deletion to the real project.
        victim = people[0]
        victim_name = sena3_sandbox.Person.GetName(victim)
        victim_guid = sena3_sandbox.Person.GetGuid(victim)
        count_before = len(people)

        assert victim_name, "Pre-existing person should have a non-empty name"

        sena3_sandbox.Person.Delete(victim)

        # Confirm: Find returns None for the deleted name, GetAll count
        # dropped by one.
        assert sena3_sandbox.Person.Find(victim_name) is None
        count_after = len(list(sena3_sandbox.Person.GetAll()))
        assert count_after == count_before - 1, (
            f"Expected {count_before - 1} persons after delete, "
            f"got {count_after}"
        )

        # The deleted GUID exists only as a sanity-check that we
        # captured something meaningful -- not used post-delete since
        # the object is gone.
        assert victim_guid is not None
